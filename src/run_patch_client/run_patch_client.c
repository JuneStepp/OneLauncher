#include <stdio.h>
#include <windows.h>

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: <patchclient.dll path> \"<args for patchclient.dll>\"\n");
        return 1;
    }

    HMODULE lib = LoadLibrary(argv[1]);
    if (lib == NULL) {
        fprintf(stderr, "Failed to load patch client DLL\n");
        return 1;
    }

    // Patch/PatchW use rundll32 style function signatures.
    // The first two arguments aren't relevant to our usage.
    typedef void (*PatchFunc)(void*, void*, const char*);
    PatchFunc Patch = (PatchFunc)GetProcAddress(lib, "Patch");
    if (Patch == NULL) {
        fprintf(stderr, "No `Patch` function found in patch client DLL\n");
        FreeLibrary(lib);
        return 1;
    }
    Patch(NULL, NULL, argv[2]);

    // Free the DLL module
    FreeLibrary(lib);
    return 0;
}
