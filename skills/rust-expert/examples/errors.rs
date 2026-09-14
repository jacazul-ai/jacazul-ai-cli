//! Errors: an enum the caller can match on, with the cause preserved.

use std::fmt;
use std::num::ParseIntError;

#[derive(Debug)]
enum PortError {
    Empty,
    NotANumber(ParseIntError),
    OutOfRange(u32),
}

impl fmt::Display for PortError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PortError::Empty => write!(f, "port is empty"),
            PortError::NotANumber(e) => write!(f, "port is not a number: {e}"),
            PortError::OutOfRange(n) => write!(f, "port {n} is out of range"),
        }
    }
}

impl std::error::Error for PortError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            PortError::NotANumber(e) => Some(e),
            _ => None,
        }
    }
}

fn parse_port(text: &str) -> Result<u16, PortError> {
    if text.is_empty() {
        return Err(PortError::Empty);
    }
    let n: u32 = text.parse().map_err(PortError::NotANumber)?;
    u16::try_from(n).map_err(|_| PortError::OutOfRange(n))
}

fn main() {
    assert_eq!(parse_port("8080").unwrap(), 8080);
    assert!(matches!(parse_port(""), Err(PortError::Empty)));
    assert!(matches!(parse_port("http"), Err(PortError::NotANumber(_))));
    assert!(matches!(parse_port("70000"), Err(PortError::OutOfRange(70000))));
    println!("ok");
}
