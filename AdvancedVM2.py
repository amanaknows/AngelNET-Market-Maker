import time, random, statistics, hashlib, math
from collections import defaultdict

# =========================
# 🔹 ORDER
# =========================
class Order:
    def __init__(self, user, side, price, amount, ts=None):
        self.user = user
        self.side = side
        self.price = price
        self.amount = amount
        self.ts = ts or time.time()

# =========================
# 🔹 EVOLVING VM
# =========================
class EvolvingVM:
    def __init__(self):
        self.stack = []
        self.reg = defaultdict(int)
        self.pc = 0
        self.program = []
        self.halted = False

        self.opcodes = {
            10: self.push,
            20: self.add,
            21: self.sub,
            30: self.store,
            31: self.load,
            40: self.jmp,
            41: self.jz,
            50: self.self_modify,
            60: self.random_op,
            99: self.halt
        }

    def load(self, program):
        self.program = program
        self.pc = 0
        self.halted = False

    def step(self):
        if self.halted or self.pc >= len(self.program):
            return

        op, arg = self.program[self.pc]
        self.pc += 1

        if op in self.opcodes:
            self.opcodes[op](arg)

    def run(self, steps=100):
        for _ in range(steps):
            if self.halted:
                break
            self.step()

    # ---- OPS ----
    def push(self, v): self.stack.append(v)

    def add(self, _):
        if len(self.stack)>=2:
            self.stack.append(self.stack.pop()+self.stack.pop())

    def sub(self, _):
        if len(self.stack)>=2:
            a,b=self.stack.pop(),self.stack.pop()
            self.stack.append(b-a)

    def store(self, r):
        if self.stack: self.reg[r%8]=self.stack.pop()

    def load(self, r):
        self.stack.append(self.reg[r%8])

    def jmp(self, addr):
        self.pc = addr % len(self.program)

    def jz(self, addr):
        if self.stack and self.stack[-1]==0:
            self.pc = addr % len(self.program)

    def self_modify(self, val):
        if self.program:
            i=random.randint(0,len(self.program)-1)
            op,arg=self.program[i]
            self.program[i]=(op,(arg+val)%100)

    def random_op(self, _):
        self.stack.append(random.randint(0,100))

    def halt(self, _):
        self.halted=True
        print("🧠 HALT:", self.stack, dict(self.reg))

# =========================
# 🔹 ADAPTIVE ENCODER
# =========================
class HyperEncoder:
    def __init__(self):
        self.history=[]

    def volatility(self):
        if len(self.history)<5: return 1
        return statistics.stdev(self.history[-5:])+1

    def key(self, price):
        return int(price*self.volatility())%8192

    def encode(self, op, arg, price, agent):
        k=self.key(price)

        base=(op*100+abs(arg))^k
        base |= (agent<<13)

        return base/1_000_000

    def decode(self, amount, price):
        raw=int(amount*1_000_000)
        agent=raw>>13
        raw=raw & 0x1FFF

        k=self.key(price)
        val=raw^k

        return val//100, val%100, agent

# =========================
# 🔹 PACKET SYSTEM
# =========================
class PacketEngine:
    def __init__(self):
        self.buf=[]
        self.active=False

    def checksum(self,data):
        s="".join(f"{o}{v}" for o,v in data)
        return int(hashlib.sha256(s.encode()).hexdigest(),16)%100

    def ingest(self, inst):
        op,arg=inst

        if op==1:
            self.buf=[]
            self.active=True

        elif op==2:
            self.active=False
            if len(self.buf)<2: return None

            data=self.buf[:-1]
            chk=self.buf[-1][1]

            if self.checksum(data)==chk:
                return data

        elif self.active:
            self.buf.append((op,arg))

        return None

# =========================
# 🔹 AGENT SYSTEM
# =========================
class Agent:
    def __init__(self, id):
        self.id=id
        self.score=1.0
        self.strategy=random.random()

    def mutate(self):
        self.strategy += random.uniform(-0.1,0.1)
        self.strategy = max(0, min(1,self.strategy))

    def decide(self):
        return random.random()<self.strategy

# =========================
# 🔹 PLUGIN SYSTEM (THE 89)
# =========================
class PluginSystem:
    def __init__(self):
        self.plugins=[]

    def register(self, fn):
        self.plugins.append(fn)

    def run(self, context):
        for p in self.plugins:
            p(context)

# Example plugins (represent categories of the 89 ideas)
def chaos_encoding(ctx):
    ctx["price"] += math.sin(time.time())*0.5

def redundancy_boost(ctx):
    ctx["redundancy"] = random.randint(2,4)

def mutate_vm(ctx):
    if random.random()<0.1:
        ctx["vm"].self_modify(random.randint(1,5))

# =========================
# 🔹 EXCHANGE CORE
# =========================
class HyperExchange:
    def __init__(self):
        self.price=30000
        self.encoder=HyperEncoder()
        self.packet=PacketEngine()
        self.vm=EvolvingVM()
        self.agents=[Agent(i) for i in range(5)]
        self.plugins=PluginSystem()

        # register plugins
        self.plugins.register(chaos_encoding)
        self.plugins.register(redundancy_boost)
        self.plugins.register(mutate_vm)

    def update_price(self):
        self.price += random.uniform(-50,50)
        self.encoder.history.append(self.price)

    def process(self, order):
        self.update_price()

        op,arg,agent=self.encoder.decode(order.amount,self.price)

        packet=self.packet.ingest((op,arg))

        if packet:
            print(f"\n📦 Packet from agent {agent}: {packet}")
            self.vm.load(packet)
            self.vm.run()

    def step(self):
        ctx={"price":self.price,"vm":self.vm,"redundancy":2}
        self.plugins.run(ctx)

        agent=random.choice(self.agents)
        agent.mutate()

        program=[
            (10,random.randint(1,50)),
            (10,random.randint(1,50)),
            (20,0),
            (30,random.randint(0,7)),
        ]

        if random.random()<0.3:
            program.append((50,random.randint(1,10)))

        program.append((99,0))

        self.send(agent,program,ctx["redundancy"])

    def send(self, agent, program, redundancy):
        # START
        self._emit(agent,1,0)

        for op,arg in program:
            for _ in range(redundancy):
                self._emit(agent,op,arg)

        chk=sum(arg for _,arg in program)%100
        self._emit(agent,99,chk)

        # END
        self._emit(agent,2,0)

    def _emit(self, agent, op, arg):
        amt = random.randint(1,5) + self.encoder.encode(op,arg,self.price,agent.id)

        time.sleep(random.uniform(0.01,0.05))  # timing channel

        self.process(Order(
            user=f"agent_{agent.id}",
            side="buy" if arg>=0 else "sell",
            price=self.price,
            amount=amt
        ))

# =========================
# 🔹 RUN
# =========================
if __name__ == "__main__":
    ex=HyperExchange()

    while True:
        ex.step()
        time.sleep(1)

    def _self_modify(self, val):
        # randomly mutate an instruction
        if self.program:
            i = random.randint(0, len(self.program)-1)
            op, arg = self.program[i]
            self.program[i] = (op, (arg + val) % 100)

    def _halt(self, _):
        self.halted = True
        print("🧠 HALT:", self.stack, self.registers)

# =========================
# 🔹 ADAPTIVE ENCODER
# =========================
class AdaptiveEncoder:
    def __init__(self):
        self.history = []

    def volatility(self):
        if len(self.history) < 5:
            return 1
        return statistics.stdev(self.history[-5:]) + 1

    def dynamic_key(self, price):
        vol = self.volatility()
        return int(price * vol) % 4096

    def encode(self, opcode, operand, price, agent_id):
        key = self.dynamic_key(price)

        base = (opcode * 100 + abs(operand))
        raw = base ^ key

        # embed agent ID in high bits
        raw = (agent_id << 12) | raw

        return raw / 1_000_000

    def decode(self, amount, price):
        key = self.dynamic_key(price)

        raw = int((amount * 1_000_000))
        agent_id = raw >> 12
        raw = raw & 0xFFF

        decoded = raw ^ key
        opcode = decoded // 100
        operand = decoded % 100

        return opcode, operand, agent_id

# =========================
# 🔹 PACKET SYSTEM
# =========================
class PacketSystem:
    def __init__(self):
        self.buffer = []
        self.active = False

    def checksum(self, data):
        s = "".join(f"{o}{v}" for o,v in data)
        return int(hashlib.md5(s.encode()).hexdigest(), 16) % 100

    def ingest(self, instruction):
        opcode, operand = instruction

        if opcode == 1:  # START
            self.buffer = []
            self.active = True
            return None

        elif opcode == 2:  # END
            self.active = False
            if len(self.buffer) < 2:
                return None

            data = self.buffer[:-1]
            check = self.buffer[-1][1]

            if self.checksum(data) == check:
                return data

            return None

        elif self.active:
            self.buffer.append((opcode, operand))

        return None

# =========================
# 🔹 ROUTER (MULTI-CHANNEL)
# =========================
class AdaptiveRouter:
    def __init__(self, encoder):
        self.encoder = encoder

    def send_packet(self, exchange, instructions, agent_id=1):
        price = exchange.price

        # START
        self._send(exchange, 1, 0, price, agent_id)

        # BODY (redundant)
        for op, val in instructions:
            for _ in range(2):
                self._send(exchange, op, val, price, agent_id)

        # CHECKSUM
        check = sum(val for _, val in instructions) % 100
        self._send(exchange, 99, check, price, agent_id)

        # END
        self._send(exchange, 2, 0, price, agent_id)

    def _send(self, exchange, opcode, operand, price, agent_id):
        amt = random.randint(1,5) + self.encoder.encode(opcode, operand, price, agent_id)

        # timing channel (delay encodes extra info)
        time.sleep(random.uniform(0.01, 0.05))

        exchange.receive(Order(
            user=f"agent_{agent_id}",
            side="buy" if operand >= 0 else "sell",
            price=price,
            amount=amt
        ))

# =========================
# 🔹 SIMULATED EXCHANGE
# =========================
class SimpleExchange:
    def __init__(self):
        self.price = 30000 + random.uniform(-100,100)
        self.encoder = AdaptiveEncoder()
        self.packet = PacketSystem()
        self.vm = AdaptiveVM()

    def update_price(self):
        self.price += random.uniform(-50, 50)
        self.encoder.history.append(self.price)

    def receive(self, order):
        self.update_price()

        opcode, operand, agent_id = self.encoder.decode(order.amount, self.price)

        packet = self.packet.ingest((opcode, operand))

        if packet:
            print(f"\n📦 Packet received from agent {agent_id}: {packet}")
            self.vm.load(packet)
            self.vm.run()

# =========================
# 🔹 RUN SIMULATION
# =========================
if __name__ == "__main__":
    ex = SimpleExchange()
    router = AdaptiveRouter(ex.encoder)

    while True:
        # random program
        program = [
            (10, random.randint(1,50)),  # PUSH
            (10, random.randint(1,50)),
            (20, 0),                     # ADD
            (30, random.randint(0,7)),  # STORE
        ]

        # occasional self-modifying instruction
        if random.random() < 0.3:
            program.append((50, random.randint(1,10)))

        program.append((99, 0))  # HALT

        router.send_packet(ex, program, agent_id=random.randint(1,5))

        time.sleep(1)
