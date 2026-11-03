{
  description = "GTNH Toolkit: factory solver and diagram generator (Python)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          # Locked pydantic-core has no build for newer Pythons, so keep uv on this one.
          UV_PYTHON = "${pkgs.python312}/bin/python";
          UV_PYTHON_DOWNLOADS = "never";

          packages = with pkgs; [
            uv # Python and dependency management
            cbc # solver binary invoked by pyomo (solver.py)
            graphviz # dot binary invoked by the graphviz package (grapher.py)
          ];
        };
      });
}
