
#define _GNU_SOURCE
#include <SDL.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>
#include <unistd.h>
SDL_Renderer *SDL_CreateRenderer(SDL_Window *window, int index, Uint32 flags) {
    SDL_Renderer *(*original)(SDL_Window*,int,Uint32)=dlsym(RTLD_NEXT,"SDL_CreateRenderer");
    SDL_Renderer *result=original(window,index,flags); int saved=errno;
    const char *path=getenv("LOOKUP_GAME_SDL_LOG");
    if (result && path) { SDL_RendererInfo info; struct timespec stamp;
        if (!SDL_GetRendererInfo(result,&info) && !clock_gettime(CLOCK_MONOTONIC,&stamp)) {
            FILE *output=fopen(path,"a"); if(output) {
                fprintf(output,"{\"pid\":%d,\"at_ns\":%lld,\"renderer\":\"%s\",\"flags\":%u,\"driver\":\"%s\"}\n",
                    getpid(),(long long)stamp.tv_sec*1000000000+stamp.tv_nsec,info.name,info.flags,SDL_GetCurrentVideoDriver());
                fclose(output);
            }
        }
    }
    errno=saved; return result;
}
SDL_GLContext SDL_GL_CreateContext(SDL_Window *window) {
    SDL_GLContext (*original)(SDL_Window*)=dlsym(RTLD_NEXT,"SDL_GL_CreateContext");
    SDL_GLContext result=original(window);int saved=errno;
    const char *path=getenv("LOOKUP_GAME_SDL_LOG");struct timespec stamp;
    if(result && SDL_GL_GetCurrentContext()==result && SDL_GL_GetCurrentWindow()==window && path) {
      const unsigned char *(*get_string)(unsigned int)=SDL_GL_GetProcAddress("glGetString");
      if(get_string && !clock_gettime(CLOCK_MONOTONIC,&stamp)) {
        const unsigned char *renderer=get_string(0x1F01),*driver=get_string(0x1F02);
        FILE *output=renderer && driver ? fopen(path,"a") : NULL;if(output) {
            fprintf(output,"{\"pid\":%d,\"at_ns\":%lld,\"operation\":\"gl_context\",\"window\":%u,\"current_window\":%u,\"window_ptr\":\"%p\",\"context_ptr\":\"%p\",\"current_context_matches\":true,\"renderer\":\"%s\",\"version\":\"%s\",\"driver\":\"%s\"}\n",
                getpid(),(long long)stamp.tv_sec*1000000000+stamp.tv_nsec,SDL_GetWindowID(window),SDL_GetWindowID(SDL_GL_GetCurrentWindow()),window,result,renderer,driver,SDL_GetCurrentVideoDriver());
            fclose(output);
        }
      }
    }
    errno=saved;return result;
}
int SDL_SetRelativeMouseMode(SDL_bool enabled) {
    int (*original)(SDL_bool)=dlsym(RTLD_NEXT,"SDL_SetRelativeMouseMode");
    int result=original(enabled);int saved=errno;
    const char *path=getenv("LOOKUP_GAME_SDL_LOG");
    struct timespec stamp;
    if(path && !clock_gettime(CLOCK_MONOTONIC,&stamp)) {
        FILE *output=fopen(path,"a");if(output) {
            fprintf(output,"{\"pid\":%d,\"at_ns\":%lld,\"operation\":\"relative\",\"requested\":%d,\"result\":%d,\"state\":%d,\"driver\":\"%s\"}\n",
                getpid(),(long long)stamp.tv_sec*1000000000+stamp.tv_nsec,enabled,result,SDL_GetRelativeMouseMode(),SDL_GetCurrentVideoDriver());
            fclose(output);
        }
    }
    errno=saved;return result;
}
void SDL_SetWindowGrab(SDL_Window *window,SDL_bool enabled) {
    void (*original)(SDL_Window*,SDL_bool)=dlsym(RTLD_NEXT,"SDL_SetWindowGrab");
    original(window,enabled);int saved=errno;
    const char *path=getenv("LOOKUP_GAME_SDL_LOG");struct timespec stamp;
    if(path && !clock_gettime(CLOCK_MONOTONIC,&stamp)) {
        FILE *output=fopen(path,"a");if(output) {
            fprintf(output,"{\"pid\":%d,\"at_ns\":%lld,\"operation\":\"grab\",\"requested\":%d,\"state\":%d,\"window\":%u,\"window_ptr\":\"%p\",\"driver\":\"%s\"}\n",
                getpid(),(long long)stamp.tv_sec*1000000000+stamp.tv_nsec,enabled,SDL_GetWindowGrab(window),SDL_GetWindowID(window),window,SDL_GetCurrentVideoDriver());
            fclose(output);
        }
    }
    errno=saved;
}
