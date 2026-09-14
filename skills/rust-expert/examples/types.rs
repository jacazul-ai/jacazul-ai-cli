//! Newtypes and enums make invalid states unrepresentable.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Cents(u64);

#[derive(Debug, PartialEq, Eq)]
enum Payment {
    Pending,
    Captured { amount: Cents },
    Refunded { amount: Cents, reason: String },
}

fn total_captured(payments: &[Payment]) -> Cents {
    let sum = payments
        .iter()
        .map(|p| match p {
            Payment::Captured { amount } => amount.0,
            Payment::Pending | Payment::Refunded { .. } => 0,
        })
        .sum();
    Cents(sum)
}

fn main() {
    let payments = [
        Payment::Pending,
        Payment::Captured { amount: Cents(250) },
        Payment::Refunded { amount: Cents(100), reason: "duplicate".into() },
        Payment::Captured { amount: Cents(50) },
    ];
    assert_eq!(total_captured(&payments), Cents(300));
    println!("ok");
}
