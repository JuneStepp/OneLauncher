{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python311;

        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

        overlay = workspace.mkPyprojectOverlay {
          # Prefer prebuilt binary wheels as a package source.
          # Sdists are less likely to "just work" because of the metadata missing from uv.lock.
          sourcePreference = "wheel";
        };
        pyprojectOverrides = final: prev: {
          onelauncher = prev.onelauncher.overrideAttrs (previousAttrs: {
            passthru = previousAttrs.passthru // {
              # Add tests to Nix package
              tests =
                let
                  virtualenv = final.mkVirtualEnv "onelauncher-pytest-env" {
                    onelauncher = [ "test" ];
                  };
                in
                (previousAttrs.tests or { })
                // {
                  pytest = pkgs.stdenv.mkDerivation {
                    name = "${final.onelauncher.name}-pytest";
                    inherit (final.onelauncher) src;
                    nativeBuildInputs = [
                      virtualenv
                    ];
                    dontConfigure = true;

                    buildPhase = ''
                      runHook preBuild

                      pytest --junitxml=report.xml

                      runHook postBuild
                    '';

                    installPhase = ''
                      runHook preInstall

                      mv report.xml $out

                      runHook postInstall
                    '';
                  };

                };
            };
          });
          zeep = prev.zeep.overrideAttrs (prevAttrs: {
            nativeBuildInputs = prevAttrs.nativeBuildInputs ++ [
              (final.resolveBuildSystem {
                setuptools = [ ];
              })
            ];
          });
          asyncache = prev.asyncache.overrideAttrs (prevAttrs: {
            nativeBuildInputs = prevAttrs.nativeBuildInputs ++ [
              (final.resolveBuildSystem {
                poetry-core = [ ];
              })
            ];
          });
          sgmllib3k = prev.sgmllib3k.overrideAttrs (prevAttrs: {
            nativeBuildInputs = prevAttrs.nativeBuildInputs ++ [
              (final.resolveBuildSystem {
                setuptools = [ ];
              })
            ];
          });
          nuitka = prev.nuitka.overrideAttrs (prevAttrs: {
            nativeBuildInputs = prevAttrs.nativeBuildInputs ++ [
              (final.resolveBuildSystem {
                setuptools = [ ];
              })
            ];
          });
          # Based on https://github.com/nix-community/poetry2nix/blob/ce2369db77f45688172384bbeb962bc6c2ea6f94/overrides/default.nix#L2915
          pyside6-essentials = prev.pyside6-essentials.overrideAttrs (
            prevAttrs:
            pkgs.lib.optionalAttrs pkgs.stdenv.isLinux {
              autoPatchelfIgnoreMissingDeps = [
                "libmysqlclient.so.21"
                "libfbclient.so.2"
                "libclntsh.so.23.1"
                "libmimerapi.so"
                "libQt6EglFsKmsGbmSupport.so*"
                "libQt6QuickShapesDesignHelpers.so.6"
                "libQt6QuickVectorImageHelpers.so.6"
                "libtiff.so.5"
              ];
              preFixup = ''
                addAutoPatchelfSearchPath ${final.shiboken6}/${final.python.sitePackages}/shiboken6
              '';
              propagatedBuildInputs = prevAttrs.propagatedBuildInputs or [ ] ++ [
                pkgs.qt6.full
                pkgs.libxkbcommon
                pkgs.gtk3
                pkgs.speechd
                pkgs.gst
                pkgs.gst_all_1.gst-plugins-base
                pkgs.gst_all_1.gstreamer
                pkgs.postgresql.lib
                pkgs.unixODBC
                pkgs.pcsclite
                pkgs.xorg.libxcb
                pkgs.xorg.xcbutil
                pkgs.xorg.xcbutilcursor
                pkgs.xorg.xcbutilerrors
                pkgs.xorg.xcbutilimage
                pkgs.xorg.xcbutilkeysyms
                pkgs.xorg.xcbutilrenderutil
                pkgs.xorg.xcbutilwm
                pkgs.libdrm
                pkgs.pulseaudio
              ];
            }
          );
        };

        # Construct package set
        pythonSet =
          # Use base package set from pyproject.nix builders.
          (pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          }).overrideScope
            (
              nixpkgs.lib.composeManyExtensions [
                pyproject-build-systems.overlays.wheel
                overlay
                pyprojectOverrides
              ]
            );
      in
      {
        packages =
          let
            inherit (pkgs.callPackages pyproject-nix.build.util { }) mkApplication;
          in
          {
            onelauncher = mkApplication {
              venv = pythonSet.mkVirtualEnv "onelauncher-env" workspace.deps.default;
              package = pythonSet.onelauncher;
            };
            default = self.packages.${system}.onelauncher;
            fhs-run =
              (pkgs.steam.override {
                extraPkgs = pkgs: [ pkgs.libz ];
                privateTmp = false;
              }).run-free;
          };
        apps = {
          onelauncher = flake-utils.lib.mkApp { drv = self.packages.${system}.onelauncher; };
          default = self.apps.${system}.onelauncher;
        };

        checks = {
          inherit (pythonSet.onelauncher.passthru.tests) pytest;
        };

        devShells.default =
          let
            editableOverlay = workspace.mkEditablePyprojectOverlay {
              # Use environment variable
              root = "$REPO_ROOT";
              # Optional: Only enable editable for these packages
              # members = [ "onelauncher" ];
            };

            editablePythonSet = pythonSet.overrideScope (
              nixpkgs.lib.composeManyExtensions [
                editableOverlay

                (final: prev: {
                  onelauncher = prev.onelauncher.overrideAttrs (old: {
                    # Filter the sources going into an editable build so the editable
                    # package doesn't have to be rebuilt on every change.
                    src = nixpkgs.lib.fileset.toSource {
                      root = old.src;
                      fileset = nixpkgs.lib.fileset.unions [
                        (old.src + "/pyproject.toml")
                        (old.src + "/README.md")
                        (old.src + "/src/onelauncher/__init__.py")
                      ];
                    };

                    # Hatchling (our build system) has a dependency on the `editables` package when building editables.
                    #
                    # In normal Python flows this dependency is dynamically handled, and doesn't need to be explicitly declared.
                    # This behavior is documented in PEP-660.
                    #
                    # With Nix the dependency needs to be explicitly declared.
                    nativeBuildInputs =
                      old.nativeBuildInputs
                      ++ final.resolveBuildSystem {
                        editables = [ ];
                      };
                  });
                })
              ]
            );

            # Enable all optional dependencies for development.
            virtualenv = editablePythonSet.mkVirtualEnv "onelauncher-dev-env" workspace.deps.all;

          in
          pkgs.mkShell {
            packages = [
              virtualenv
              pkgs.innoextract
              (pkgs.runCommand "onelauncher-shell-completions"
                {
                  nativeBuildInputs = [
                    self.packages.${system}.onelauncher
                    pkgs.installShellFiles
                  ];
                }
                ''
                  installShellCompletion --cmd onelauncher \
                      --bash <(onelauncher generate-shell-completion bash) \
                      --fish <(onelauncher generate-shell-completion fish) \
                      --zsh <(onelauncher generate-shell-completion zsh)
                ''
              )
              pkgs.uv
              # Used for Nuitka compilation caching
              pkgs.ccache
            ];

            env = {
              # Don't create venv using `uv`.
              UV_NO_SYNC = "1";

              UV_PYTHON = pythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";

              # Used in OneLauncher script
              NIX_PYTHON_ENV = "${virtualenv}";
            };

            shellHook = ''
              # Undo dependency propagation by nixpkgs.
              unset PYTHONPATH

              # Get repository root using git. This is expanded at runtime by the editable `.pth` machinery.
              export REPO_ROOT=$(git rev-parse --show-toplevel)

              # Help IDEs find the right Python environment
              ln --force --no-target-directory --symbolic "${virtualenv}" ./.venv

              ln --force --symbolic "${
                pkgs.callPackage ./src/run_patch_client { }
              }/bin/run_ptch_client.exe" ./src/onelauncher/external/run_ptch_client.exe
            '';
          };
      }
    );
}
