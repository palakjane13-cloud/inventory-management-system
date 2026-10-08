const $ = (s) => document.querySelector(s);
const rows = $("#rows"), msg = $("#msg");

function say(text, ok) {
  msg.textContent = text;
  msg.className = ok ? "ok" : "err";
}

async function api(url, method = "GET", body) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function load() {
  const q = $("#search").value.trim();
  try {
    const items = await api("/api/products?q=" + encodeURIComponent(q));
    render(items);
    const all = q ? await api("/api/products") : items;
    const low = all.filter((p) => p.low_stock);
    $("#stats").textContent = `${all.length} products`;
    $("#alerts").hidden = !low.length;
    $("#alerts").innerHTML = low.length
      ? `<strong>Low stock (10 or fewer):</strong> ${low.map((p) => `${esc(p.name)} (${p.quantity})`).join(", ")}`
      : "";
  } catch (e) { say(e.message); }
}

function render(items) {
  if (!items.length) {
    rows.innerHTML = '<tr><td colspan="6" class="empty">No products found. Add one above or change your search.</td></tr>';
    return;
  }
  rows.innerHTML = items.map((p) => `
    <tr class="${p.low_stock ? "low" : ""}" data-id="${p.id}">
      <td>${esc(p.product_id)}</td><td>${esc(p.name)}</td><td>${esc(p.category)}</td>
      <td><input class="q" type="number" min="0" step="1" value="${p.quantity}" aria-label="Quantity">
          ${p.low_stock ? '<span class="badge">Low</span>' : ""}</td>
      <td><input class="pr" type="number" min="0" step="0.01" value="${p.price}" aria-label="Price"></td>
      <td class="act"><button class="ghost" data-a="save">Save</button><button class="danger" data-a="del">Delete</button></td>
    </tr>`).join("");
}

$("#addForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(e.target));
  try {
    await api("/api/products", "POST", body);
    e.target.reset();
    say("Product added", true);
    load();
  } catch (err) { say(err.message); }
});

rows.addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  const tr = btn.closest("tr"), id = tr.dataset.id;
  try {
    if (btn.dataset.a === "save") {
      await api("/api/products/" + id, "PUT", {
        quantity: tr.querySelector(".q").value,
        price: tr.querySelector(".pr").value,
      });
      say("Product updated", true);
    } else if (confirm("Delete this product?")) {
      await api("/api/products/" + id, "DELETE");
      say("Product deleted", true);
    } else return;
    load();
  } catch (err) { say(err.message); }
});

let t;
$("#search").addEventListener("input", () => { clearTimeout(t); t = setTimeout(load, 250); });
load();
