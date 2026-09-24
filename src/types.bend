import Base

type Lane is Data:
  W{lo: U32, hi: U32}

type State is Data:
  S{a0: Lane, a1: Lane, a2: Lane, a3: Lane, a4: Lane, a5: Lane, a6: Lane, a7: Lane, a8: Lane, a9: Lane, a10: Lane, a11: Lane, a12: Lane, a13: Lane, a14: Lane, a15: Lane, a16: Lane, a17: Lane, a18: Lane, a19: Lane, a20: Lane, a21: Lane, a22: Lane, a23: Lane, a24: Lane}

# A state in interleaved form: lane k as its even bits e{k} and its odd bits o{k}.
type St is Data:
  St{e0: U32, o0: U32, e1: U32, o1: U32, e2: U32, o2: U32, e3: U32, o3: U32, e4: U32, o4: U32, e5: U32, o5: U32, e6: U32, o6: U32, e7: U32, o7: U32, e8: U32, o8: U32, e9: U32, o9: U32, e10: U32, o10: U32, e11: U32, o11: U32, e12: U32, o12: U32, e13: U32, o13: U32, e14: U32, o14: U32, e15: U32, o15: U32, e16: U32, o16: U32, e17: U32, o17: U32, e18: U32, o18: U32, e19: U32, o19: U32, e20: U32, o20: U32, e21: U32, o21: U32, e22: U32, o22: U32, e23: U32, o23: U32, e24: U32, o24: U32}
