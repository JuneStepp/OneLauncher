{ pkgsCross }:
pkgsCross.mingw32.stdenv.mkDerivation {
  name = "run-patch-client";

  src = ./.;

  installPhase = ''
    mkdir -p $out/bin

    cp run_ptch_client.exe $out/bin/
  '';
}
