{
  description = "A nix flake for hops";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
  };

  outputs = { self , nixpkgs ,... }: let
    # system should match the system you are running on
    system = "x86_64-linux";
  in {
    devShells."${system}".default = let
      pkgs = import nixpkgs {
        inherit system;
      };
    in pkgs.mkShell {
      name = "hops";
      packages = with pkgs; [
        python312Full
        python312Packages.pip
        pre-commit
        gnumake
      ];
    };
  };
}