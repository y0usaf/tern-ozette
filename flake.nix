{
  description = "tern-ozette: CSS for Tern's Ozette, YoRHa, Grok and Mini looks";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    systems = ["x86_64-linux" "aarch64-linux"];
    forAll = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
  in {
    apps = forAll (pkgs: let
      lookcheck = pkgs.writeShellApplication {
        name = "lookcheck";
        runtimeInputs = [(pkgs.python3.withPackages (ps: [ps.numpy ps.pillow])) pkgs.procps pkgs.bash];
        text = ''
          [ -f check/lookcheck.py ] || { echo "lookcheck: run from the tern-ozette checkout" >&2; exit 2; }
          exec python3 check/lookcheck.py "$@"
        '';
      };
    in {
      default = {
        type = "app";
        program = "${lookcheck}/bin/lookcheck";
      };
    });
  };
}
