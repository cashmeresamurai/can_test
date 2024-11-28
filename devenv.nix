{ pkgs, ... }:

{
  packages = with pkgs; [
    python3
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
    # Add GTK dependencies
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
  ];

  languages.python = {
    enable = true;
    version = "3.11";
    venv = {
      enable = true;
      requirements = ''
      python-can
      customtkinter
      netifaces
      pyserial
      pysnmplib
      pyftdi
      fastapi
      jinja2
      uvicorn
      pygobject
      pycairo
      result
      python-multipart
      maturin
      '';
    };
  };

  # Set environment variables
  env = {
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH";
    # Add GI environment variables
    GI_TYPELIB_PATH = "${pkgs.gtk3}/lib/girepository-1.0:${pkgs.gobject-introspection}/lib/girepository-1.0";
  };

  enterShell = ''
    echo "Python environment ready!"
  '';
}
