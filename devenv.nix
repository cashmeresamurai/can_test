{ pkgs, ... }:

{
  packages = with pkgs; [
    stdenv.cc.cc.lib
    pyright
    lsof
    tcpdump
    python3Packages.pyftdi
    lazygit
    ripgrep
    python3Packages.fastapi
    python3Packages.jinja2
    python3Packages.uvicorn
    gobject-introspection
    python3Packages.pygobject3
    python3Packages.pycairo
    python3Packages.tkinter
    python3Packages.result
    tk
    glib
    gvfs
    gnome.adwaita-icon-theme
    llvmPackages_12.clang-unwrapped
    linuxHeaders
    cargo
  ];

  languages.python = {
    enable = true;
    version = "3.11";
  };

  env = {
    # UV_PYTHON = "${pkgs.python311}/bin/python3.11";
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH";
    LIBCLANG_PATH = "${pkgs.llvmPackages_12.clang-unwrapped.lib}/lib";
    BINDGEN_EXTRA_CLANG_ARGS = "-I${pkgs.linuxHeaders}/include";
  };

  enterShell = ''
    if [ ! -d ".venv" ]; then
      source .venv/bin/activate
      uv pip install -r requirements.txt
      uv sync
    fi
    source .venv/bin/activate
  '';
}
