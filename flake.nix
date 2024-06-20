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
        vkbeautify = super.vkbeautify.overridePythonAttrs (old: {
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
        packages = [pkgs.poetry];
        shellHook = ''
          # There can be Qt version mismatches, if the Qt version in PySide6 tries to
          # access the nixpkgs Qt plugins found in QT_PLUGIN_PATH.
          unset QT_PLUGIN_PATH
          # Trick pyside6-designer into setting the right LD_PRELOAD path for Python
          # instead of the bare library name.
          export PYENV_ROOT=${poetry_env}
        '';
      };
    });
}
