const BASE_URL = "/api";

export async function fetchProducts() {
  const res = await fetch(`${BASE_URL}/products`);
  if (!res.ok) {
    throw new Error(`Failed to load products (${res.status})`);
  }
  return res.json();
}

export async function fetchRecommendations(query) {
  const res = await fetch(`${BASE_URL}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }

  return data;
}
