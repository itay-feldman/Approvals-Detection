# Stage 1
Assuming an ERC20 (compliant) token is in question

## Question: Explain in your own words what is an approval, and what are the differences between a `transfer` to a `transferFrom` function.

## Answer:

### Approval
An approval is when a caller (the message sender) tells the ERC20 contract that another account (the spender) is allowed to use a certain amount the caller's balance. This means that from now on the spender account has an allowance of `amount` from the caller's balance

### The `transfer` function
The ERC20 `transer` function, as its name suggests, is responsible for transferring a specified amount of funds from the sender to a specified destination account. It is worth noting that no approval (besides the sender issuing the request) is required here.

### The `transferFrom` function
The `transferFrom` function, on its surface, operates like an extended `transfer` function. It allows you to not only specify a destination account and amount of tokens, but also a source account. The kicker here is that this function deducts this amount from the caller's (not source or destination!) allowance. So the source account would have had to approve the transfer's amount (or more) as the allowance of the caller. This is somewhat similar to a power of attorney given to the caller by the source account, so the caller can transfer `amount` tokens out of the source account into the destination account at the caller's own discretion.
