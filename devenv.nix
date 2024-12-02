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
    gtk4
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
  ];

  languages.rust.enable = true;
  languages.python = {
    enable = true;
    version = "3.11";
    uv = {
      enable = true;
      sync = {
        enable = true;
        extras = [
          "python-can"
          "customtkinter"
          "netifaces"
          "pyserial"
          "pysnmplib"
          "pyftdi"
          "fastapi"
          "jinja2"
          "uvicorn"
          "pygobject"
          "pycairo"
          "result"
          "python-multipart"
          "maturin"
        ];
      };
    };
  };

  env = {
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH";
    GI_TYPELIB_PATH = "${pkgs.gtk3}/lib/girepository-1.0:${pkgs.gobject-introspection}/lib/girepository-1.0";
    LIBCLANG_PATH = "${pkgs.llvmPackages_12.clang-unwrapped.lib}/lib";
    BINDGEN_EXTRA_CLANG_ARGS = "-I${pkgs.linuxHeaders}/include";
  };

  enterShell = ''
    echo "Python environment ready with uv!"
  '';
}
