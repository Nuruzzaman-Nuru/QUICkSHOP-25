class NegotiationBot:
    def __init__(self, product):
        self.product = product
        self.min_price = product.min_price
        self.max_price = product.price
        self.max_discount = product.max_discount_percentage / 100
        self.negotiation_rounds = 0
        self.last_offer = None
        self.last_counter = None
        
        # Strategy parameters
        self.eagerness = 0.7  # How eager to make a deal (0-1)
        self.flexibility = 0.6  # How flexible in counteroffer (0-1)
        
    def evaluate_offer(self, offered_price):
        """
        Evaluate a customer's offer and decide to accept, reject, or counter
        Returns: (decision, counter_offer, message)
        decision: 'accept', 'reject', or 'counter'
        counter_offer: float or None
        message: str explanation
        """
        self.negotiation_rounds += 1
        self.last_offer = offered_price
        
        # Quick rejects
        if offered_price >= self.max_price:
            return 'reject', None, "Please use the regular price if you're willing to pay full price."
        
        if offered_price < self.min_price:
            return 'reject', None, f"I'm sorry, but {offered_price:.2f} is too low. The minimum price is {self.min_price:.2f}"
            
        # Calculate metrics
        discount = (self.max_price - offered_price) / self.max_price
        if discount > self.max_discount:
            return 'reject', None, f"That's too low. The maximum discount we can offer is {self.max_discount*100:.0f}%"
        
        # Decision making
        if self._should_accept(offered_price):
            return 'accept', None, "Great! We have a deal!"
            
        counter_offer = self._calculate_counter_offer()
        self.last_counter = counter_offer
        return 'counter', counter_offer, self._get_counter_message(counter_offer)
        
    def _should_accept(self, offered_price):
        """Determine if an offer should be accepted"""
        # More likely to accept as rounds increase
        round_factor = min(self.negotiation_rounds / 5, 1)
        
        # More likely to accept if close to target price
        price_factor = (offered_price - self.min_price) / (self.max_price - self.min_price)
        
        # Combined acceptance probability
        acceptance_prob = (round_factor + price_factor + self.eagerness) / 3
        
        return acceptance_prob > 0.8
        
    def _calculate_counter_offer(self):
        """Calculate a counter-offer based on the negotiation state"""
        if not self.last_offer:
            # Initial counter offer
            discount = self.max_discount * (1 - self.eagerness)
            return self.max_price * (1 - discount)
            
        # Calculate middle ground, weighted by flexibility
        target = self.last_offer + (self.max_price - self.last_offer) * self.flexibility
        
        # Ensure counter offer is within bounds
        return max(min(target, self.max_price), self.min_price)
        
    def _get_counter_message(self, counter_offer):
        """Generate a message for the counter offer"""
        discount = (self.max_price - counter_offer) / self.max_price * 100
        
        messages = [
            f"How about {counter_offer:.2f}? That's a {discount:.1f}% discount.",
            f"I can offer it for {counter_offer:.2f}. That's quite a good deal!",
            f"Let's meet in the middle at {counter_offer:.2f}?",
            f"I can go down to {counter_offer:.2f}. What do you think?"
        ]
        
        return messages[self.negotiation_rounds % len(messages)]
    
    def continue_iteration(self):
        """Check if negotiation should continue based on rounds and price difference"""
        # Maximum rounds check
        if self.negotiation_rounds >= 5:
            return False
            
        # Check if price difference is too small to continue
        if self.last_offer and abs(self.last_counter - self.last_offer) < 1.0:
            return False
            
        # Check if we're still within reasonable discount range
        if self.last_offer and (self.max_price - self.last_offer) / self.max_price > self.max_discount:
            return False
            
        return True

    def negotiate(self, user_offer):
        """Process user offer and generate counter-offer"""
        self.last_offer = user_offer
        self.negotiation_rounds += 1
        
        if not self.continue_iteration():
            return None  # Indicates negotiation should end
            
        # Calculate counter-offer based on existing strategy
        self.last_counter = self._calculate_counter_offer(user_offer)
        return self.last_counter

def create_negotiation_session(product):
    """Create a new negotiation session for a product"""
    if not product.is_negotiable():
        raise ValueError("This product is not available for negotiation")
    
    return NegotiationBot(product)

def process_negotiation(negotiation, offered_price):
    """
    Process a negotiation offer and return the result
    Returns: dict with keys:
    - accepted: bool
    - counter_price: float or None
    - message: str
    """
    bot = create_negotiation_session(negotiation.product)
    decision, counter_offer, message = bot.evaluate_offer(offered_price)
    
    return {
        'accepted': decision == 'accept',
        'counter_price': counter_offer,
        'message': message
    }