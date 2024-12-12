{ config, pkgs, ... }:
{
  # Enable SNMP service
  # Install SNMP package
  environment.systemPackages = with pkgs; [
    net-snmp
  ];
  users.users.nix = {
    isNormalUser = true;
    extraGroups = [ "dialout" "tty" "video" ];
  };

  # Zusätzliche udev-Regeln für USB-Geräte
  services.udev.extraRules = ''
    KERNEL=="ttyUSB[0-9]*", GROUP="dialout", MODE="0660"
  '';
  # Configure SNMP service
  systemd.services.snmpd = {
    enable = true;
    wantedBy = [ "multi-user.target" ];
    description = "Net-SNMP daemon";
    after = [ "network.target" ];
    restartIfChanged = true;
    serviceConfig = {
      User = "root";
      Group = "root";
      Restart = "always";
      ExecStart = "${pkgs.net-snmp}/bin/snmpd -Lf /var/log/snmpd.log -f -c /etc/snmp/snmpd.conf";
    };
  };

  # Configure SNMP configuration file
  environment.etc."snmp/snmpd.conf".text = ''
    # Allow SNMPv1 and SNMPv2c
    rocommunity public localhost
    rwcommunity root localhost

    # Full access for root community
    com2sec local     localhost       root
    com2sec local2    localhost      public

    group MyRWGroup v1         local
    group MyROGroup v1         local2

    view all    included  .1
    view system included  .1.3.6.1.2.1.1
    # Add VScom specific OIDs
    view all    included  .1.3.6.1.4.1.12695

    # Give read-write access to MyRWGroup
    access MyRWGroup ""      any       noauth    exact  all    all    all
    access MyROGroup ""      any       noauth    exact  all    none   none

    # Enable write access
    rwuser root

    syslocation "Your Location"
    syscontact "Admin <admin@example.com>"
    sysservices 72

    # Add enterprise specific settings
    pass .1.3.6.1.4.1.12695 /bin/sh /usr/local/bin/pass_persist.sh
  '';

  # Open firewall ports
  networking.firewall.allowedUDPPorts = [ 161 162 ];

  # Create required directories
  systemd.tmpfiles.rules = [
    "d /etc/snmp 0644 root root -"
    "d /var/lib/net-snmp 0600 root root -"
  ];
  boot.kernelModules = [ "ftdi_sio" ]; # Add FTDI serial module

  # Add kernel packages
  boot.kernelPackages = pkgs.linuxPackages_latest;

  # Enable kernel module loading
  boot.supportedFilesystems = [ "vfat" "ext4" ];

  # Add necessary hardware support
  hardware.enableAllFirmware = true;
}
