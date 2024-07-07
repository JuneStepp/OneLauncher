{
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";
  inputs.poetry2nix = {
    url = "github:nix-community/poetry2nix";
    inputs.nixpkgs.follows = "nixpkgs";
    inputs.flake-utils.follows = "flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    poetry2nix,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      p2n = import poetry2nix {inherit pkgs;};
      python = pkgs.python311;
      overrides = p2n.defaultPoetryOverrides.extend (self: super: {
        pyside6-essentials = super.pyside6-essentials.overridePythonAttrs (old: {
          autoPatchelfIgnoreMissingDeps = (old.autoPatchelfIgnoreMissingDeps or []) ++ ["libgbm.so.1"];
        });
        pysidesix-frameless-window = super.pysidesix-frameless-window.overridePythonAttrs (old: {
          buildInputs = (old.buildInputs or []) ++ [super.setuptools];
        });
        asyncache = super.asyncache.overridePythonAttrs (old: {
          buildInputs = (old.buildInputs or []) ++ [super.poetry-core];
        });
        trio-typing = super.trio-typing.overridePythonAttrs (old: {
          buildInputs = (old.buildInputs or []) ++ [super.setuptools];
        });
        backports-tarfile = super.backports-tarfile.overridePythonAttrs (old: {
          buildInputs = (old.buildInputs or []) ++ [super.setuptools];
        });
      });

      # use impure flake in direnv to get live editing for mkPoetryEnv
      envProjectDir = builtins.getEnv "PROJECT_DIR";
      srcDir =
        if envProjectDir == ""
        then ./src
        else "${envProjectDir}/src";
      poetry_env = p2n.mkPoetryEnv {
        inherit python;
        projectDir = self;
        inherit overrides;
        extras = [];

        editablePackageSources.onelauncher = srcDir;
      };
      poetry_app = p2n.mkPoetryApplication {
        inherit python;
        projectDir = self;
        inherit overrides;
        extras = [];
      };
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      packages = {
        onelauncher = poetry_app;
        default = self.packages.${system}.onelauncher;
      };
      devShells.default = pkgs.mkShell {
        inputsFrom = [poetry_env.env];
        packages = [
          pkgs.poetry
          # Used for Nuitka compilation caching
          pkgs.ccache
        ];
        shellHook = ''
          # Include both the PySide6 Qt and system Qt plugin paths in QT_PLUGIN_PATH.
          # The system plugins are included, so apps can follow the system theme. The
          # PySide6 Qt plugins path has to be manually included if QT_PLUGIN_PATH exists.
          export QT_PLUGIN_PATH=${poetry_env}/${poetry_env.python.sitePackages}/PySide6/Qt/plugins:$QT_PLUGIN_PATH
          # Used in OneLauncher script
          export NIX_PYTHON_ENV=${poetry_env}
        '';
      };
      # The FHS environment can be used for testing compiled builds of OneLauncher, as 
      # well as the WINE binaies that get downloaded by default.
      devShells.fhs =
        (pkgs.buildFHSUserEnv
          {
            name = "fhs-shell";
            targetPkgs = pkgs:
              [
                # Generic dependencies for Nuitka binaries
                pkgs.glibc
                pkgs.libz
                # So Qt can run on Wayland
                pkgs.wayland
              ]
              # Dependencies for Qt to run
              ++ pkgs.kdePackages.qtbase.propagatedBuildInputs
              # Dependencies for WINE to run
              ++ pkgs.wine64.buildInputs;
            # Needed to run 32-bit executables with WINE
            multiArch = true;
            multiPkgs = pkgs: [pkgs.glibc] ++ pkgs.wine64.buildInputs;
          })
        .env;
    });
}
