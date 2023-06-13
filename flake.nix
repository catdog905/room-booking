{
  description = "Room booking system at Innopolis University.";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.pre-commit-hooks.url = "github:cachix/pre-commit-hooks.nix";
  inputs.poetry2nix = {
    url = "github:nix-community/poetry2nix";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, pre-commit-hooks, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        inherit (poetry2nix.legacyPackages.${system}) mkPoetryEnv;
        pkgs = nixpkgs.legacyPackages.${system};

        # Inherit project configuration from poetry
        app = mkPoetryEnv {
          python = pkgs.python311;
          projectDir = ./.;
          editablePackageSources = {
            app = ./app;
          };
        };
      in
      {
        checks = {
          pre-commit-check = pre-commit-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              # Format *.nix files
              nixpkgs-fmt.enable = true;

              # Format *.py files
              black.enable = true;

              # Conventional commits with commitizen
              commitizen.enable = true;
            };
          };
        };

        devShells.default = pkgs.mkShell {
          inherit (self.checks.${system}.pre-commit-check) shellHook;

          inputsFrom = [ app.env ];
        };
      });
}
