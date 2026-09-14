//! Legible control flow: `?`, `let else`, and a final successful expression.

use std::collections::HashMap;

#[derive(Debug, PartialEq)]
enum RunError {
    MissingKey(&'static str),
    BadValue(std::num::ParseIntError),
}

impl From<std::num::ParseIntError> for RunError {
    fn from(e: std::num::ParseIntError) -> Self {
        RunError::BadValue(e)
    }
}

fn workers(config: &HashMap<&str, &str>) -> Result<usize, RunError> {
    let Some(raw) = config.get("workers") else {
        return Err(RunError::MissingKey("workers"));
    };
    let n: usize = raw.parse()?;
    Ok(n.clamp(1, 64))
}

fn main() {
    let mut config = HashMap::new();
    assert_eq!(workers(&config), Err(RunError::MissingKey("workers")));
    config.insert("workers", "x");
    assert!(matches!(workers(&config), Err(RunError::BadValue(_))));
    config.insert("workers", "200");
    assert_eq!(workers(&config), Ok(64));
    println!("ok");
}
