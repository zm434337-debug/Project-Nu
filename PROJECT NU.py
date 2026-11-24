import math
import re
import tkinter as tk
from tkinter import ttk, messagebox


ALLOWED = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "exp": math.exp, "log": math.log, "ln": math.log, "log10": math.log10,
    "sqrt": math.sqrt, "abs": abs, "pi": math.pi, "e": math.e,
}


def make_func(text):
    """يحوّل نص مثل '2x^2 - e^(-x)' إلى دالة بايثون آمنة f(x)."""
    s = text.strip().replace("^", "**").replace("×", "*").replace("−", "-")
    if not s:
        raise ValueError("الدالة فارغة")
    # ضرب ضمني: 2x -> 2*x ، 3(x+1) -> 3*(x+1) ، )( -> )*( ، x( -> x*(
    s = re.sub(r"(\d|\))\s*(?=[a-zA-Z(])", r"\1*", s)
    s = re.sub(r"\)\s*(?=\d)", r")*", s)
    s = re.sub(r"\bx\s*(?=\()", "x*", s)
    s = re.sub(r"\bx\s+(?=[a-zA-Z0-9])", "x*", s)
    code = compile(s, "<expr>", "eval")
    for name in code.co_names:
        if name != "x" and name not in ALLOWED:
            raise ValueError(f"اسم غير مسموح: {name}")
    env = {"__builtins__": {}, **ALLOWED}
    return lambda x: float(eval(code, env, {"x": x}))


def derivative(f, x, h=1e-6):
    return (f(x + h) - f(x - h)) / (2 * h)


def newton(f, df, x0, tol, max_iter):
    rows, x = [], x0
    for i in range(1, max_iter + 1):
        fx, dfx = f(x), df(x)
        if abs(dfx) < 1e-14:
            return rows, x, "توقف: المشتقة تساوي صفر تقريباً"
        nx = x - fx / dfx
        err = abs(nx - x)
        rows.append((i, x, fx, nx, err))
        x = nx
        if err < tol:
            return rows, x, f"تم التقارب بعد {i} تكرار"
        if abs(x) > 1e12:
            return rows, x, "تباعد: القيم كبرت جداً"
    return rows, x, f"وصلنا لأقصى عدد تكرارات ({max_iter}) بدون تقارب"


def fixed_point(g, x0, tol, max_iter):
    rows, x = [], x0
    for i in range(1, max_iter + 1):
        nx = g(x)
        err = abs(nx - x)
        rows.append((i, x, nx, nx, err))
        x = nx
        if err < tol:
            return rows, x, f"تم التقارب بعد {i} تكرار"
        if abs(x) > 1e12:
            return rows, x, "تباعد: القيم كبرت جداً"
    return rows, x, f"وصلنا لأقصى عدد تكرارات ({max_iter}) بدون تقارب"


# ---------------------------------------------------------------- الواجهة

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("حاسبة التحليل العددي")
        self.geometry("760x560")
        self.minsize(640, 480)

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 15, "bold"))
        style.configure("Result.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=6)

        self.method = tk.StringVar(value="newton")
        self.f_var = tk.StringVar(value="x^3 - x - 2")
        self.df_var = tk.StringVar()
        self.x0_var = tk.StringVar(value="1.5")
        self.tol_var = tk.StringVar(value="1e-6")
        self.iter_var = tk.StringVar(value="50")

        self.last = None
        self._build()
        self._on_method()

    def _build(self):
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="حاسبة التحليل العددي", style="Title.TLabel").pack(anchor="w")

        # اختيار الطريقة
        m = ttk.Frame(root)
        m.pack(fill="x", pady=(10, 4))
        ttk.Radiobutton(m, text="نيوتن - رافسون", variable=self.method,
                        value="newton", command=self._on_method).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(m, text="النقطة الثابتة", variable=self.method,
                        value="fixed", command=self._on_method).pack(side="left")

        # المدخلات
        form = ttk.LabelFrame(root, text="المدخلات", padding=10)
        form.pack(fill="x", pady=6)
        form.columnconfigure(1, weight=1)

        self.f_label = ttk.Label(form, text="f(x) =")
        self.f_label.grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(form, textvariable=self.f_var).grid(row=0, column=1, columnspan=5, sticky="ew", padx=6)

        self.df_label = ttk.Label(form, text="f'(x) (اختياري) =")
        self.df_label.grid(row=1, column=0, sticky="w", pady=3)
        self.df_entry = ttk.Entry(form, textvariable=self.df_var)
        self.df_entry.grid(row=1, column=1, columnspan=5, sticky="ew", padx=6)

        ttk.Label(form, text="x₀").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(form, textvariable=self.x0_var, width=10).grid(row=2, column=1, sticky="w", padx=6)
        ttk.Label(form, text="Tolerance").grid(row=2, column=2, sticky="e")
        ttk.Entry(form, textvariable=self.tol_var, width=10).grid(row=2, column=3, padx=6)
        ttk.Label(form, text="أقصى تكرارات").grid(row=2, column=4, sticky="e")
        ttk.Entry(form, textvariable=self.iter_var, width=6).grid(row=2, column=5, padx=6)

        btns = ttk.Frame(root)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="احسب", style="Accent.TButton", command=self.solve).pack(side="left")
        ttk.Button(btns, text="مسح", command=self.clear).pack(side="left", padx=8)
        self.bind("<Return>", lambda _e: self.solve())

        # النتيجة
        self.result = ttk.Label(root, text="", style="Result.TLabel", wraplength=700)
        self.result.pack(anchor="w", pady=(4, 6))

        # تبويبات: الرسم + الجدول
        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True)

        plot_tab = ttk.Frame(self.nb)
        self.nb.add(plot_tab, text="الرسم")
        self.canvas = tk.Canvas(plot_tab, bg="white", highlightthickness=0, height=260)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.draw_plot())

        table_tab = ttk.Frame(self.nb)
        self.nb.add(table_tab, text="الجدول")
        cols = ("n", "x", "val", "next", "err")
        self.tree = ttk.Treeview(table_tab, columns=cols, show="headings", height=10)
        for c, w in zip(cols, (50, 150, 150, 150, 140)):
            self.tree.column(c, width=w, anchor="center")
        sb = ttk.Scrollbar(table_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _on_method(self):
        newton_mode = self.method.get() == "newton"
        if newton_mode:
            self.f_label.config(text="f(x) =")
            self.df_label.grid()
            self.df_entry.grid()
            self.f_var.set("x^3 - x - 2")
            self.x0_var.set("1.5")
            heads = ("#", "xₙ", "f(xₙ)", "xₙ₊₁", "|xₙ₊₁ − xₙ|")
        else:
            self.f_label.config(text="g(x) =")
            self.df_label.grid_remove()
            self.df_entry.grid_remove()
            self.f_var.set("cos(x)")
            self.x0_var.set("0.5")
            heads = ("#", "xₙ", "g(xₙ)", "xₙ₊₁", "|xₙ₊₁ − xₙ|")
        for c, h in zip(("n", "x", "val", "next", "err"), heads):
            self.tree.heading(c, text=h)
        self.clear()

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.result.config(text="")
        self.last = None
        self.draw_plot()

    def solve(self):
        self.clear()
        try:
            f = make_func(self.f_var.get())
            x0 = float(self.x0_var.get())
            tol = float(self.tol_var.get())
            max_iter = int(self.iter_var.get())
            if self.method.get() == "newton":
                d = self.df_var.get().strip()
                df = make_func(d) if d else (lambda x: derivative(f, x))
                rows, root, msg = newton(f, df, x0, tol, max_iter)
            else:
                rows, root, msg = fixed_point(f, x0, tol, max_iter)
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
            return

        for n, x, v, nx, err in rows:
            self.tree.insert("", "end", values=(n, f"{x:.8f}", f"{v:.6e}" if self.method.get() == "newton" else f"{v:.8f}",
                                                f"{nx:.8f}", f"{err:.3e}"))
        if rows:
            self.tree.yview_moveto(1)
        self.result.config(text=f"{msg}\nالنتيجة: x* ≈ {root:.8f}")
        self.last = (self.method.get(), f, rows, root)
        self.nb.select(0)
        self.draw_plot()

    # ------------------------------------------------------------ الرسم
    def draw_plot(self):
        c = self.canvas
        c.delete("all")
        W, H = c.winfo_width(), c.winfo_height()
        if W < 80 or H < 80:
            return
        if not self.last:
            c.create_text(W / 2, H / 2, fill="#888", font=("Segoe UI", 11),
                          text="اضغط «احسب» لعرض الرسم")
            return

        method, f, rows, root = self.last
        newton_mode = method == "newton"
        L, R, T, B = 55, 15, 15, 30

        # مدى x من نقاط التكرار
        pts = [rows[0][1]] + [r[3] for r in rows] + [root]
        pts = [v for v in pts if math.isfinite(v) and abs(v) < 1e9]
        lo, hi = min(pts), max(pts)
        pad = max((hi - lo) * 0.3, 0.5)
        lo, hi = lo - pad, hi + pad

        # عينات المنحنى
        N = 300
        xs = [lo + (hi - lo) * k / N for k in range(N + 1)]
        ys = []
        for x in xs:
            try:
                y = f(x)
                ys.append(y if math.isfinite(y) else None)
            except Exception:
                ys.append(None)
        vals = sorted(v for v in ys if v is not None)
        if not vals:
            c.create_text(W / 2, H / 2, text="تعذر رسم الدالة في هذا المدى", fill="#c00")
            return
        a = vals[int(0.02 * (len(vals) - 1))]
        b = vals[int(0.98 * (len(vals) - 1))]
        extra = [0.0] if newton_mode else [lo, hi]
        ylo, yhi = min([a] + extra), max([b] + extra)
        if yhi - ylo < 1e-12:
            ylo, yhi = ylo - 1, yhi + 1
        m = (yhi - ylo) * 0.08
        ylo, yhi = ylo - m, yhi + m
        big = (yhi - ylo) * 3

        def px(x):
            return L + (x - lo) / (hi - lo) * (W - L - R)

        def py(y):
            y = max(min(y, yhi + big), ylo - big)
            return H - B - (y - ylo) / (yhi - ylo) * (H - T - B)

        # شبكة + أرقام المحاور
        for k in range(6):
            gx = lo + (hi - lo) * k / 5
            gy = ylo + (yhi - ylo) * k / 5
            c.create_line(px(gx), T, px(gx), H - B, fill="#eee")
            c.create_line(L, py(gy), W - R, py(gy), fill="#eee")
            c.create_text(px(gx), H - B + 12, text=f"{gx:.3g}", fill="#666", font=("Segoe UI", 8))
            c.create_text(L - 6, py(gy), text=f"{gy:.3g}", fill="#666", anchor="e", font=("Segoe UI", 8))
        c.create_rectangle(L, T, W - R, H - B, outline="#bbb")
        if ylo < 0 < yhi:
            c.create_line(L, py(0), W - R, py(0), fill="#555")
        if lo < 0 < hi:
            c.create_line(px(0), T, px(0), H - B, fill="#555")

        # المنحنى (يتقطع عند النقاط غير المعرفة)
        seg = []
        for x, y in zip(xs, ys):
            if y is None:
                if len(seg) >= 4:
                    c.create_line(*seg, fill="#1f6feb", width=2)
                seg = []
            else:
                seg += [px(x), py(y)]
        if len(seg) >= 4:
            c.create_line(*seg, fill="#1f6feb", width=2)

        if newton_mode:
            for i, x, fx, nx, _err in rows:
                c.create_line(px(x), py(0), px(x), py(fx), fill="#aaa", dash=(3, 3))
                c.create_line(px(x), py(fx), px(nx), py(0), fill="#e8590c", width=1.5)
                c.create_oval(px(x) - 3, py(0) - 3, px(x) + 3, py(0) + 3, fill="#e8590c", outline="")
                if i <= 5:
                    c.create_text(px(x), py(0) + 12, text=f"x{i - 1}", fill="#e8590c", font=("Segoe UI", 8))
            ry = 0
            legend = "الأزرق: f(x)   البرتقالي: المماسات"
        else:
            c.create_line(px(lo), py(lo), px(hi), py(hi), fill="#888", dash=(4, 3))
            for _i, x, gx, _nx, _err in rows:
                c.create_line(px(x), py(x), px(x), py(gx), fill="#e8590c", width=1.5)
                c.create_line(px(x), py(gx), px(gx), py(gx), fill="#e8590c", width=1.5)
            ry = root
            legend = "الأزرق: g(x)   الرمادي: y = x   البرتقالي: مسار التكرار"

        # الجذر
        rx, rpy = px(root), py(ry)
        c.create_oval(rx - 5, rpy - 5, rx + 5, rpy + 5, fill="#2f9e44", outline="white")
        c.create_text(L + 8, T + 10, anchor="w", text=legend, fill="#444", font=("Segoe UI", 9))


if __name__ == "__main__":
    App().mainloop()
