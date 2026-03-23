import time, random, statistics, heapq, hashlib, requests

# =========================
# 🔹 ORDER OBJECT
# =========================
class Order:
    def __init__(self, user, side, price, amount, timestamp=None):
        self.user = user
        self.side = side
        self.price = price
        self.amount = amount
        self.timestamp = timestamp or time.time()

# =========================
# 🔹 AMM POOL
# =========================
class AMMPool:
    def __init__(self, reserve_a, reserve_b):
        self.reserve_a = reserve_a
        self.reserve_b = reserve_b
        self.k = reserve_a * reserve_b

    def get_quote(self, amount_in, is_buy=True):
        if is_buy:
            new_b = self.reserve_b + amount_in
            new_a = self.k / new_b
            out = self.reserve_a - new_a
            self.reserve_a, self.reserve_b = new_a, new_b
            return out
        else:
            new_a = self.reserve_a + amount_in
            new_b = self.k / new_a
            out = self.reserve_b - new_b
            self.reserve_a, self.reserve_b = new_a, new_b
            return out

# =========================
# 🔹 SECRET VM (UPGRADED)
# =========================
class SecretVM:
    def __init__(self, key=1337):
        self.stack = []
        self.registers = {i: 0 for i in range(8)}
        self.key = key

        self.opcodes = {
            10: self._push,
            20: self._add,
            21: self._sub,
            30: self._store,
            31: self._load,
            99: self._halt
        }

    def decode(self, amount):
        encoded = int((amount * 1_000_000) % 10_000)
        decoded = encoded ^ self.key
        opcode = decoded // 100
        operand = decoded % 100
        return opcode, operand

    def execute_from_order(self, order):
        opcode, operand = self.decode(order.amount)

        if opcode in self.opcodes:
            self.opcodes[opcode](operand)

    def _push(self, val):
        self.stack.append(val)

    def _add(self, _):
        if len(self.stack) >= 2:
            self.stack.append(self.stack.pop() + self.stack.pop())

    def _sub(self, _):
        if len(self.stack) >= 2:
            a, b = self.stack.pop(), self.stack.pop()
            self.stack.append(b - a)

    def _store(self, reg):
        if self.stack:
            self.registers[reg % 8] = self.stack.pop()

    def _load(self, reg):
        self.stack.append(self.registers[reg % 8])

    def _halt(self, _):
        print("🧠 VM HALT →", self.stack, self.registers)

# =========================
# 🔹 EXCHANGE CORE
# =========================
class AdvancedExchange:
    def __init__(self, symbol):
        self.symbol = symbol
        self.bids = []  # max heap
        self.asks = []  # min heap
        self.logs = []
        self.oracles = []
        self.price_history = []

        self.amm = AMMPool(1000, 1000)
        self.vm = SecretVM()

    # ---------- ORACLES ----------
    def add_oracle(self, func, weight=1.0):
        self.oracles.append((func, weight))

    def get_price(self):
        prices = []
        for func, weight in self.oracles:
            try:
                p = func()
                prices.extend([p] * int(weight * 10))
            except:
                continue

        if not prices:
            return 1.0

        price = statistics.median(prices)
        self.price_history.append(price)
        return price

    # ---------- ORDER BOOK ----------
    def place_order(self, order):
        self.vm.execute_from_order(order)

        if order.side == "buy":
            heapq.heappush(self.bids, (-order.price, order))
        else:
            heapq.heappush(self.asks, (order.price, order))

        self.match()

    def match(self):
        while self.bids and self.asks:
            best_bid_price, bid = self.bids[0]
            best_ask_price, ask = self.asks[0]

            best_bid_price = -best_bid_price

            if best_bid_price < best_ask_price:
                break

            size = min(bid.amount, ask.amount)
            bid.amount -= size
            ask.amount -= size

            self.logs.append(f"TRADE {size:.4f} @ {best_ask_price:.2f}")

            if bid.amount <= 0:
                heapq.heappop(self.bids)
            if ask.amount <= 0:
                heapq.heappop(self.asks)

    # ---------- SMART ROUTING ----------
    def execute_trade(self, side, amount):
        price = self.get_price()

        order = Order("user", side, price, amount)
        self.place_order(order)

        # fallback to AMM if not filled
        if amount > 0:
            received = self.amm.get_quote(amount, is_buy=(side == "buy"))
            self.logs.append(f"AMM {side} {amount:.4f} → {received:.4f}")

    # ---------- DISPLAY ----------
    def render(self):
        print("\033c", end="")  # clear terminal
        price = self.get_price()

        best_bid = -self.bids[0][0] if self.bids else 0
        best_ask = self.asks[0][0] if self.asks else 0

        print(f"=== {self.symbol} EXCHANGE ===")
        print(f"Price: ${price:.4f}")
        print(f"Spread: {best_ask - best_bid:.4f}")
        print(f"AMM Liquidity: {self.amm.reserve_a:.2f}")
        print("-" * 40)

        for log in self.logs[-6:]:
            print(">", log)

# =========================
# 🔹 LIVE ORACLE (BINANCE)
# =========================
def binance_oracle(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    return float(requests.get(url, timeout=2).json()["price"])

# fallback oracle (noise)
def local_oracle():
    return 30000 + random.uniform(-100, 100)

# =========================
# 🔹 STEALTH ROUTER
# =========================
class StealthRouter:
    def __init__(self, exchange):
        self.exchange = exchange

    def send_hidden(self, cmd, val):
        base = random.randint(1, 5)

        # encode opcode
        encoded = ((cmd * 100) + val) ^ 1337
        suffix = encoded / 1_000_000

        qty = base + suffix

        # chaff
        for _ in range(random.randint(2, 4)):
            self.exchange.place_order(
                Order("noise", "buy",
                      random.uniform(29000, 31000),
                      random.uniform(0.1, 1))
            )

        # real hidden command
        self.exchange.place_order(
            Order("stealth", "buy", 30000, qty)
        )

# =========================
# 🔹 SIMULATION LOOP
# =========================
if __name__ == "__main__":
    ex = AdvancedExchange("BTC/USD")

    # add oracles (user-controlled)
    ex.add_oracle(local_oracle, weight=1)

    try:
        ex.add_oracle(lambda: binance_oracle(), weight=2)
    except:
        pass

    router = StealthRouter(ex)

    while True:
        # simulate real-ish trading
        side = random.choice(["buy", "sell"])
        amt = random.uniform(0.01, 0.5)

        ex.execute_trade(side, amt)

        # occasionally send hidden command
        if random.random() < 0.2:
            router.send_hidden(cmd=10, val=random.randint(1, 50))  # PUSH

        ex.render()
        time.sleep(1)
