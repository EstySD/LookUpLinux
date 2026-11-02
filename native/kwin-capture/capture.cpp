// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2010 Martin Graesslin
// SPDX-FileCopyrightText: 2021 Vlad Zahorodnii
// SPDX-FileCopyrightText: 2025 Xaver Hugl
// The offscreen rendering sequence follows KWin's GPL-2.0-or-later screenshot
// plugin (Vlad Zahorodnii, Martin Graesslin, Xaver Hugl), KWin 6.8.1.
#include <plugin.h>
#include <input.h>
#include <input_event.h>
#include <input_event_spy.h>
#include <cursor.h>
#include <workspace.h>
#include <wayland_server.h>
#include <main.h>
#include <compositor.h>
#include <core/output.h>
#include <core/outputlayer.h>
#include <core/renderdevice.h>
#include <core/inputdevice.h>
#include <opengl/eglcontext.h>
#include <opengl/glframebuffer.h>
#include <opengl/gltexture.h>
#include <scene/workspacescene.h>
#include <scene/windowitem.h>
#include <window.h>
#include <KConfigGroup>
#include <KSharedConfig>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QDBusContext>
#include <QDBusReply>
#include <QDBusUnixFileDescriptor>
#include <QFileSystemWatcher>
#include <QImage>
#include <QKeySequence>
#include <QStandardPaths>
#include <QTimer>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <deque>

using namespace KWin;

namespace {
constexpr qsizetype MaxBytes = 256 << 20;
qint64 nowNs()
{
    return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
}

class SnapshotLayer : public OutputLayer
{
public:
    SnapshotLayer(LogicalOutput *output, GLFramebuffer *buffer)
        : OutputLayer(output->backendOutput(), OutputLayerType::Primary), m_buffer(buffer) {}
    FormatModifierMap supportedDrmFormats() const override { return {}; }
    std::optional<OutputLayerBeginFrameInfo> beginFrame(OutputFrame *) override
    {
        if (!m_buffer->context()->makeCurrent()) return std::nullopt;
        return OutputLayerBeginFrameInfo{RenderTarget(m_buffer), Region::infinite()};
    }
    bool endFrame(const Region &, const Region &, OutputFrame *) override { return true; }
    void releaseBuffers() override {}
private:
    GLFramebuffer *m_buffer;
};

QImage snapshot(LogicalOutput *output, uint hiddenPid)
{
    auto device = Compositor::self()->primaryDevice();
    if (!device) return {};
    auto context = device->eglContext();
    if (!context || !context->makeCurrent()) return {};
    const QSize size = (output->geometryF().size() * output->scale()).toSize();
    if (size.isEmpty() || size.width() > 16384 || size.height() > 16384
        || qint64(size.width()) * size.height() * 4 > MaxBytes) return {};
    auto texture = GLTexture::allocate(GL_RGBA8, size);
    if (!texture) return {};
    GLFramebuffer buffer(texture.get());
    if (!buffer.valid()) return {};
    SnapshotLayer layer(output, &buffer);
    if (!layer.preparePresentationTest()) return {};
    SceneView view(kwinApp()->scene(), output, nullptr, &layer, device);
    ItemTreeView cursor(&view, kwinApp()->scene()->cursorItem(), output, nullptr, nullptr);
    cursor.setExclusive(true);
    view.addWindowFilter([hiddenPid](Window *window) {
        return window->excludeFromCapture() || (hiddenPid && window->pid() == hiddenPid);
    });
    view.setViewport(output->geometryF());
    view.setScale(output->scale());
    view.prePaint();
    const auto finish = qScopeGuard([&view] { view.postPaint(); });
    auto begin = layer.beginFrame(nullptr);
    if (!begin) return {};
    const Rect damage(QPoint(), size);
    view.paint(begin->renderTarget, QPoint(), damage);
    if (!layer.endFrame(damage, damage, nullptr)) return {};
    QImage image(size, QImage::Format_RGBX8888);
    if (image.isNull()) return {};
    GLFramebuffer::pushFramebuffer(&buffer);
    context->glReadnPixels(0, 0, size.width(), size.height(), GL_RGBA, GL_UNSIGNED_BYTE,
                          image.sizeInBytes(), image.bits());
    GLFramebuffer::popFramebuffer();
    image.flip(Qt::Vertical);
    return image;
}
}

class LookupCapture : public Plugin, public InputEventSpy, protected QDBusContext
{
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.lookup.Capture")
public:
    LookupCapture()
    {
        m_config = KSharedConfig::openConfig(QStringLiteral("kglobalshortcutsrc"));
        m_positions.push_back({nowNs() / 1000, Cursors::self()->mouse()->pos()});
        m_path = QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation) + "/kglobalshortcutsrc";
        reload();
        connect(&m_watch, &QFileSystemWatcher::fileChanged, this, [this] {
            QTimer::singleShot(50, this, [this] { reload(); });
        });
        m_expiry.setSingleShot(true);
        connect(&m_expiry, &QTimer::timeout, this, [this] {
            if (m_image.isNull()) m_metadata.clear();
            else {
                m_image = {};
                m_metadata = {{"error", "expired"}};
            }
        });
        connect(waylandServer(), &WaylandServer::lockStateChanged, this, [this] { clear(); });
        auto bus = QDBusConnection::sessionBus();
        bus.registerObject("/org/lookup/Capture", this, QDBusConnection::ExportAllSlots);
        m_registered = bus.registerService("org.lookup.Capture");
        if (m_registered) input()->installInputEventSpy(this);
    }
    ~LookupCapture() override
    {
        if (m_registered) {
            auto bus = QDBusConnection::sessionBus();
            bus.unregisterObject("/org/lookup/Capture");
            bus.unregisterService("org.lookup.Capture");
        }
    }
    void pointerMotion(PointerMotionEvent *event) override
    {
        m_positions.push_back({event->timestamp.count(), event->position});
        if (m_positions.size() > 128) m_positions.pop_front();
    }
    void keyboardKey(KeyboardKeyEvent *event) override
    {
        if (event->state != KeyboardKeyState::Pressed || waylandServer()->isScreenLocked()) return;
        const auto key = QKeyCombination(event->modifiersRelevantForGlobalShortcuts, event->key).toCombined();
        if (!m_keys.contains(key)) return;
        clear();
        m_metadata = {{"error", "capture_failed"}};
        const qint64 entered = nowNs();
        // Different input devices can be dispatched out of timestamp order.
        // A later pointer event must not replace the key event's coordinates.
        std::optional<Position> position;
        for (const auto &candidate : m_positions) {
            if (candidate.at <= event->timestamp.count() && (!position || candidate.at >= position->at))
                position = candidate;
        }
        if (!position) return;
        const QPointF point = position->point;
        auto output = workspace()->outputAt(point);
        if (!output) return;
        const auto owner = QDBusConnection::sessionBus().interface()->servicePid("org.lookup.Linux");
        m_image = snapshot(output, owner.isValid() ? owner.value() : 0);
        if (m_image.isNull()) return;
        const auto geometry = output->geometryF();
        const auto available = workspace()->clientArea(MaximizeArea, output);
        m_metadata = {{"type", "raw"}, {"format", int(m_image.format())},
            {"width", m_image.width()}, {"height", m_image.height()}, {"stride", m_image.bytesPerLine()},
            {"scale", output->scale()}, {"name", output->name()}, {"x", geometry.x()}, {"y", geometry.y()},
            {"logical_width", geometry.width()}, {"logical_height", geometry.height()},
            {"cursor_x", point.x()}, {"cursor_y", point.y()},
            {"pointer_ns", qlonglong(position->at * 1000)},
            {"latest_pointer_ns", qlonglong(m_positions.back().at * 1000)},
            {"available_x", available.x()}, {"available_y", available.y()},
            {"available_width", available.width()}, {"available_height", available.height()},
            {"input_ns", qlonglong(event->timestamp.count() * 1000)}, {"capture_ns", nowNs()},
            {"capture_ms", (nowNs() - entered) / 1e6}};
        m_expiry.start(5000);
    }
public Q_SLOTS:
    int Version() const { return 1; }
    QVariantMap Take()
    {
        const auto bus = QDBusConnection::sessionBus();
        if (!calledFromDBus()) return {};
        const auto owner = bus.interface()->serviceOwner("org.lookup.Linux");
        if (!owner.isValid() || owner.value() != message().service()) return {};
        if (waylandServer()->isScreenLocked()) { clear(); return {}; }
        if (m_image.isNull()) {
            const auto result = m_metadata;
            if (!result.isEmpty() && result.value("status") != "consumed") consumed();
            return result;
        }
        if (!m_expiry.isActive()) { consumed(); return {{"error", "expired"}}; }
        const int fd = memfd_create("lookup-hotkey", MFD_CLOEXEC | MFD_ALLOW_SEALING);
        if (fd < 0) { consumed(); return {{"error", "capture_failed"}}; }
        const auto bytes = m_image.sizeInBytes();
        qsizetype offset = 0;
        while (offset < bytes) {
            const auto written = write(fd, m_image.constBits() + offset, bytes - offset);
            if (written <= 0) { close(fd); consumed(); return {{"error", "capture_failed"}}; }
            offset += written;
        }
        lseek(fd, 0, SEEK_SET);
        if (fcntl(fd, F_ADD_SEALS, F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL) < 0) {
            close(fd); consumed(); return {{"error", "capture_failed"}};
        }
        auto result = m_metadata;
        result.insert("fd", QVariant::fromValue(QDBusUnixFileDescriptor(fd)));
        close(fd);
        consumed();
        return result;
    }
private:
    void clear() { m_expiry.stop(); m_image = {}; m_metadata.clear(); }
    void consumed()
    {
        m_image = {};
        m_metadata = {{"status", "consumed"}};
        m_expiry.start(5000);
    }
    void reload()
    {
        m_config->reparseConfiguration();
        const auto entry = m_config->group("services").group("org.lookup.Linux.desktop")
                               .readEntry("_launch", QStringList{});
        m_keys.clear();
        for (const auto &text : entry.value(0).split('\t')) {
            const auto sequence = QKeySequence::fromString(text, QKeySequence::PortableText);
            if (sequence.count() == 1 && !sequence.isEmpty()) m_keys.append(sequence[0].toCombined());
        }
        if (!m_watch.files().contains(m_path)) m_watch.addPath(m_path);
    }
    KSharedConfig::Ptr m_config;
    QFileSystemWatcher m_watch;
    QString m_path;
    QList<int> m_keys;
    QTimer m_expiry;
    QImage m_image;
    QVariantMap m_metadata;
    bool m_registered = false;
    struct Position { qint64 at; QPointF point; };
    std::deque<Position> m_positions;
};

class LookupFactory : public PluginFactory
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID PluginFactory_iid FILE "metadata.json")
    Q_INTERFACES(KWin::PluginFactory)
public:
    std::unique_ptr<Plugin> create() const override { return std::make_unique<LookupCapture>(); }
};
#include "capture.moc"
