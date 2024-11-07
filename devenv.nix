{ pkgs, ... }:

{
  # Enable devenv shell features
  packages = with pkgs; [
    python3
    stdenv.cc.cc.lib
    pyright
    lazygit
    ripgrep
  ];

  languages.javascript.enable = true;
  languages.python = {
    enable = true;
    version = "3.11";
    venv = {
      enable = true;
      requirements = ''
      python-can
      netifaces
      pyserial
      '';
    };
  };

  # Set environment variables
  env.LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH";

  # Enter the environment
  enterShell = ''
    echo "Python environment ready!"
  '';
}
