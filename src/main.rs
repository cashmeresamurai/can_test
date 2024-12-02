use linuxfb::{self, Framebuffer};

fn main() {
    let fb = linuxfb::Framebuffer::new("/dev/fb0").unwrap();

    println!("Size in pixels: {:?}", fb.get_size());

    println!("Bytes per pixel: {:?}", fb.get_bytes_per_pixel());

    println!("Physical size in mm: {:?}", fb.get_physical_size());

    // Map the framebuffer into memory, so we can write to it:
    let mut data = fb.map().unwrap();

    // Make everything black:
    for i in 0..data.len() {
        data[i] = 0;
    }

    // Make everything white:
    for i in 0..data.len() {
        data[i] = 0xFF;
    }
}
