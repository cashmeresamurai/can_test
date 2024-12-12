import pymonctl as pmc
from pprint import pprint
from result import Ok, Err, Result


async def check_vga_adapter() -> Result[pmc.ScreenValue, str]:
    vgas = pmc.getAllMonitorsDict()
    pprint(f"len vgas: {len(vgas)}")
    match len(vgas):
        case 2:
            vga: pmc.ScreenValue = vgas["DP-2"]
            return Ok(vga)
        case 1:
            return Err("Der DP-VGA Adapter konnte nicht gefunden werden.")
            # vga_1: pmc.ScreenValue = vgas["eDP-1"]
            # return Ok(vga_1)
        case _:
            return Err("error no displays found")
