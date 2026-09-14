//! Ownership: borrow for scoped access, move for transfer, clone on purpose.

/// Borrows the list; the caller keeps ownership.
fn longest(words: &[String]) -> Option<&str> {
    words.iter().map(String::as_str).max_by_key(|w| w.len())
}

/// Consumes the list and returns owned data the caller now owns.
fn into_upper(words: Vec<String>) -> Vec<String> {
    words.into_iter().map(|w| w.to_uppercase()).collect()
}

fn main() {
    let words = vec!["zig".to_string(), "rust".to_string()];
    let best = longest(&words).map(str::to_owned);
    let shouted = into_upper(words); // `words` is moved here
    assert_eq!(best.as_deref(), Some("rust"));
    assert_eq!(shouted, ["ZIG", "RUST"]);
    println!("ok");
}
