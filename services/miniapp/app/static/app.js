/* global Telegram */
const state = {
  initData: "",
  contractorIdDebug: null,
  me: null,
  currentOrderId: null,
  currentOrder: null
};

function qs(name){
  return new URLSearchParams(location.search).get(name);
}

function setStatus(text){
  document.getElementById("status").textContent = text;
}

function tabActivate(tabName){
  document.querySelectorAll(".tab").forEach(b => b.classList.toggle("active", b.dataset.tab===tabName));
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  const map = {
    orders: "view-orders",
    order: "view-order",
    property: "view-property",
    profile: "view-profile"
  };
  document.getElementById(map[tabName]).classList.add("active");
}

async function api(path, options = {}){
  const headers = options.headers || {};
  if (state.initData){
    headers["X-Telegram-Init-Data"] = state.initData;
  }
  if (state.contractorIdDebug){
    headers["X-Debug-User-Id"] = String(state.contractorIdDebug);
  }
  headers["Content-Type"] = headers["Content-Type"] || "application/json";
  const res = await fetch(path, { ...options, headers });
  if (!res.ok){
    const txt = await res.text();
    throw new Error(`${res.status} ${txt}`);
  }
  return res.json();
}

function escapeHtml(s){
  return (s||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

function card(title, bodyHtml){
  return `<div class="card"><div class="h">${escapeHtml(title)}</div>${bodyHtml}</div>`;
}

function kv(k, v){
  return `<div class="kv"><span class="k">${escapeHtml(k)}:</span> ${v}</div>`;
}

function renderOrders(){
  const el = document.getElementById("view-orders");
  if (!state.me) return;
  const orders = state.me.orders || [];
  if (!orders.length){
    el.innerHTML = card("Заказы", `<p class="p">Вам пока не назначены заказы.</p>`);
    return;
  }
  const list = orders.map(o => `
    <div class="item">
      <div class="item-title">${escapeHtml(o.order_id)}</div>
      <div class="item-sub">${o.chat_link ? `<a href="${escapeHtml(o.chat_link)}" target="_blank">Открыть чат</a>` : "Чат не задан"}</div>
      <div style="margin-top:10px">
        <button class="btn full" data-open-order="${escapeHtml(o.order_id)}">Открыть</button>
      </div>
    </div>
  `).join("");
  el.innerHTML = card("Ваши заказы", `<div class="list">${list}</div>`);
  el.querySelectorAll("[data-open-order]").forEach(btn => {
    btn.addEventListener("click", () => openOrder(btn.dataset.openOrder));
  });
}

function renderOrder(){
  const el = document.getElementById("view-order");
  const order = state.currentOrder;
  if (!order){
    el.innerHTML = card("Заказ", `<p class="p">Выберите заказ во вкладке «Заказы».</p>`);
    return;
  }
  const o = order.order;
  const files = order.files || [];
  const stages = order.stages || [];

  const filesHtml = files.length ? files.map(f => `<div class="item">
    <div class="item-title">${escapeHtml(f.name || "Файл")}</div>
    <div class="item-sub"><a href="${escapeHtml(f.url)}" target="_blank">${escapeHtml(f.url)}</a></div>
  </div>`).join("") : `<p class="p">Файлы не прикреплены.</p>`;

  const stagesHtml = stages.length ? stages.map(s => {
    const value = (o.stages_display_mode === "sums")
      ? `${s.amount ?? "—"} руб.`
      : `${s.hours ?? "—"} ч.`;
    return `<div class="item">
      <div class="row">
        <div class="item-title">${new Date(s.date).toLocaleString()}</div>
        <div class="item-title">${escapeHtml(value)}</div>
      </div>
      <div class="item-sub">${escapeHtml(s.comment || "")}</div>
    </div>`;
  }).join("") : `<p class="p">Этапов пока нет.</p>`;

  const addBtn = (!o.stages_readonly && o.stages_display_mode === "hours")
    ? `<button id="addStageBtn" class="btn full">Добавить этап</button>`
    : `<p class="p">Добавление этапов отключено для этого заказа.</p>`;

  el.innerHTML = [
    card("Детали", [
      kv("ID заказа", `<b>${escapeHtml(o.order_id)}</b>`),
      kv("Чат", o.chat_link ? `<a href="${escapeHtml(o.chat_link)}" target="_blank">Открыть</a>` : "—"),
      kv("Отображение этапов", escapeHtml(o.stages_display_mode === "sums" ? "суммами" : "трудочасами")),
      `<div style="margin-top:10px">${addBtn}</div>`
    ].join("")),
    card("ТЗ", `<p class="p">${escapeHtml(o.tz_text || "—")}</p>`),
    card("Условия", `<p class="p">${escapeHtml(o.terms_text || "—")}</p>`),
    card("Файлы", `<div class="list">${filesHtml}</div>`),
    card("Этапы", `<div class="list">${stagesHtml}</div>`)
  ].join("");

  const add = el.querySelector("#addStageBtn");
  if (add){
    add.addEventListener("click", () => openStageDialog(o.order_id));
  }
}

function renderProperty(){
  const el = document.getElementById("view-property");
  const order = state.currentOrder;
  if (!order){
    el.innerHTML = card("Имущество", `<p class="p">Откройте заказ, чтобы увидеть имущество.</p>`);
    return;
  }
  const props = order.properties || [];
  const body = props.length ? props.map(p => `
    <div class="item">
      <div class="row">
        <div class="item-title">${escapeHtml(p.name)}</div>
        <div class="item-title">×${p.quantity}</div>
      </div>
      <div class="item-sub">${escapeHtml(p.comment || "")}</div>
    </div>
  `).join("") : `<p class="p">Имущество не числится.</p>`;
  el.innerHTML = card("Имущество под ответственностью", `<div class="list">${body}</div>`);
}

function renderProfile(){
  const el = document.getElementById("view-profile");
  if (!state.me){
    el.innerHTML = card("Профиль", `<p class="p">…</p>`);
    return;
  }
  const c = state.me.contractor;
  el.innerHTML = card("Профиль", `
    <div class="kv"><span class="k">Telegram ID:</span> <b>${c.tg_id}</b></div>
    <div class="kv"><span class="k">Текущая сумма аванса:</span> <b>${c.advance_amount} руб.</b></div>

    <label class="kv"><span class="k">Как с вами связаться</span>
      <textarea id="contactInfo" rows="3" placeholder="Телефон / email / @username">${escapeHtml(c.contact_info || "")}</textarea>
    </label>

    <label class="kv"><span class="k">Как вам оплачивать</span>
      <textarea id="paymentInfo" rows="3" placeholder="Реквизиты">${escapeHtml(c.payment_info || "")}</textarea>
    </label>

    <div style="margin-top:10px">
      <button id="saveProfileBtn" class="btn full">Сохранить</button>
    </div>
  `);

  el.querySelector("#saveProfileBtn").addEventListener("click", async () => {
    try{
      setStatus("Сохранение…");
      const contact = el.querySelector("#contactInfo").value;
      const pay = el.querySelector("#paymentInfo").value;
      await api("/api/app/profile", { method: "PUT", body: JSON.stringify({ contact_info: contact, payment_info: pay }) });
      setStatus("Сохранено ✅");
      await loadMe();
    }catch(e){
      setStatus("Ошибка сохранения");
      alert(e.message);
    }
  });
}

async function loadMe(){
  state.me = await api("/api/app/me", { method:"GET", headers: { "Content-Type": "application/json" } });
  renderOrders();
  renderProfile();
}

async function openOrder(orderId){
  try{
    setStatus("Загрузка заказа…");
    state.currentOrderId = orderId;
    state.currentOrder = await api(`/api/app/orders/${encodeURIComponent(orderId)}`, { method:"GET" });
    renderOrder();
    renderProperty();
    tabActivate("order");
    setStatus("Готово");
  }catch(e){
    setStatus("Ошибка");
    alert(e.message);
  }
}

function openStageDialog(orderId){
  const dlg = document.getElementById("stageDialog");
  const hours = document.getElementById("stageHours");
  const comment = document.getElementById("stageComment");
  hours.value = "";
  comment.value = "";
  dlg.showModal();

  const submit = document.getElementById("stageSubmit");
  const onClick = async () => {
    try{
      setStatus("Сохранение этапа…");
      const payload = { hours: Number(hours.value || 0), comment: comment.value || null };
      await api(`/api/app/orders/${encodeURIComponent(orderId)}/stages`, { method:"POST", body: JSON.stringify(payload) });
      dlg.close();
      await openOrder(orderId);
      setStatus("Этап добавлен ✅");
    }catch(e){
      setStatus("Ошибка");
      alert(e.message);
    }finally{
      submit.removeEventListener("click", onClick);
    }
  };
  submit.addEventListener("click", onClick);
}

function bindTabs(){
  document.querySelectorAll(".tab").forEach(b => {
    b.addEventListener("click", () => {
      const t = b.dataset.tab;
      tabActivate(t);
      if (t==="orders") renderOrders();
      if (t==="order") renderOrder();
      if (t==="property") renderProperty();
      if (t==="profile") renderProfile();
    });
  });
}

async function boot(){
  bindTabs();
  tabActivate("orders");

  const tg = window.Telegram && Telegram.WebApp ? Telegram.WebApp : null;
  if (tg){
    tg.ready();
    tg.expand();
    state.initData = tg.initData || "";
  } else {
    // non-telegram browser: allow dev auth via query ?debug_user_id=
    const d = qs("debug_user_id");
    if (d) state.contractorIdDebug = Number(d);
  }

  try{
    setStatus("Загрузка…");
    await loadMe();
    const preOrder = qs("order_id");
    if (preOrder) await openOrder(preOrder);
    setStatus("Готово ✅");
  }catch(e){
    setStatus("Ошибка авторизации/загрузки");
    console.error(e);
    alert(e.message);
  }
}

boot();
