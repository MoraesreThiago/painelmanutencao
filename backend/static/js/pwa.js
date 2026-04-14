if ("serviceWorker" in navigator) {
  window.addEventListener("load", async () => {
    if (window.APP_DEBUG) {
      try {
        const registrations = await navigator.serviceWorker.getRegistrations();
        await Promise.all(registrations.map((registration) => registration.unregister()));
        const cacheKeys = await caches.keys();
        await Promise.all(cacheKeys.map((key) => caches.delete(key)));
      } catch (error) {
        console.error("Falha ao limpar service workers em desenvolvimento", error);
      }
      return;
    }

    navigator.serviceWorker.register("/sw.js").catch((error) => {
      console.error("Falha ao registrar o service worker", error);
    });
  });
}

const DB_NAME = "sgm_offline";
const STORE_NAME = "outbox";

function openOutboxDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "local_id", autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function waitForTransaction(tx) {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

async function addOutboxItem(item) {
  const db = await openOutboxDb();
  const tx = db.transaction(STORE_NAME, "readwrite");
  tx.objectStore(STORE_NAME).add(item);
  await waitForTransaction(tx);
}

async function listOutboxItems() {
  const db = await openOutboxDb();
  const tx = db.transaction(STORE_NAME, "readonly");
  return new Promise((resolve, reject) => {
    const request = tx.objectStore(STORE_NAME).getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

async function clearOutboxItem(id) {
  const db = await openOutboxDb();
  const tx = db.transaction(STORE_NAME, "readwrite");
  tx.objectStore(STORE_NAME).delete(id);
  await waitForTransaction(tx);
}

async function flushOutbox() {
  if (!navigator.onLine) return;
  const items = await listOutboxItems();
  if (!items.length) return;

  const payload = {
    items: items.map((item) => ({
      entity_name: item.entity_name,
      entity_id: item.entity_id || null,
      action: item.action,
      payload: item.payload,
    })),
  };

  const response = await fetch("/api/v1/sync/outbox/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) return;
  for (const item of items) {
    await clearOutboxItem(item.local_id);
  }
}

window.SGMPWA = {
  addOutboxItem,
  flushOutbox,
};

window.addEventListener("online", () => {
  flushOutbox().catch((error) => console.error("Falha ao sincronizar outbox", error));
});
