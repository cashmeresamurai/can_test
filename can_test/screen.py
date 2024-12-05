from typing_extensions import Any, Dict, List
import pymonctl as pmc
import time
from pprint import pprint
from result import Ok, Err, Result


def check_vga_adapter() -> Result[pmc.ScreenValue, str]:
    monitors = pmc.getAllMonitorsDict()
    pprint(f"len monitors: {len(monitors)}")
    match len(monitors):
        case 2:
            monitor: pmc.ScreenValue = monitors["DP-2"]
            return Ok(monitor)
        case _:
            return Err("Der DP-VGA Adapter konnte nicht gefunden werden. Bitte stellen Sie sicher dass Sie die Anweisungen richtig befolgt haben.")


if __name__ == "__main__":
    main()
