//! Scoped threads: borrow the data, every thread joined before return.

use std::sync::Mutex;
use std::thread;

fn squares(input: &[u64]) -> Vec<u64> {
    let out = Mutex::new(vec![0; input.len()]);
    thread::scope(|s| {
        for (i, n) in input.iter().enumerate() {
            let out = &out;
            s.spawn(move || {
                let value = n * n;
                out.lock().unwrap()[i] = value;
            });
        }
    });
    out.into_inner().unwrap()
}

fn main() {
    assert_eq!(squares(&[0, 1, 2, 3]), [0, 1, 4, 9]);
    println!("ok");
}
