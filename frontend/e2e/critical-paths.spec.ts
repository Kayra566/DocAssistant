import { expect, test } from "@playwright/test";

/** Her koşuda benzersiz kullanıcı üretir; testler birbirini etkilemez. */
function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

const PASSWORD = "Tr0ub4dour&3xample!";

test("landing page yönlendirmeleri ve yasal sayfalar çalışır", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  await page.getByRole("link", { name: /Gizlilik|Privacy/ }).first().click();
  await expect(page).toHaveURL(/\/privacy/);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
});

test("çerez banner'ı seçim sonrası kaybolur", async ({ page }) => {
  await page.goto("/");

  const banner = page.getByRole("region");
  await expect(banner).toBeVisible();

  await page.getByRole("button", { name: /Yalnızca zorunlu|Essential only/ }).click();
  await expect(banner).toBeHidden();

  await page.reload();
  await expect(page.getByRole("region")).toBeHidden();
});

test("kayıt → doküman yükleme → AI özeti → dışa aktarma akışı", async ({ page }) => {
  const email = uniqueEmail("e2e");

  await page.goto("/register");
  await page.getByLabel(/E-?posta|Email/i).fill(email);
  await page.getByLabel(/Parola|Password/i).first().fill(PASSWORD);
  await page.getByRole("button", { name: /Kayıt|Register|Hesap/i }).click();

  await expect(page).toHaveURL(/\/(dashboard|verify-email|login)/, {
    timeout: 20_000,
  });

  if (page.url().includes("/login")) {
    await page.getByLabel(/E-?posta|Email/i).fill(email);
    await page.getByLabel(/Parola|Password/i).first().fill(PASSWORD);
    await page.getByRole("button", { name: /Giriş|Sign in|Login/i }).click();
  }

  await page.goto("/dashboard");
  await expect(page.getByText(email)).toBeVisible({ timeout: 20_000 });

  await page.getByRole("link", { name: /Dokümanlar|Documents/ }).first().click();
  await expect(page).toHaveURL(/\/documents/);

  await page.setInputFiles('input[type="file"]', {
    name: "e2e-rapor.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(
      "Rapor 01.03.2025 tarihinde yayimlandi. Toplam butce 250000 TL olarak onaylandi.",
    ),
  });

  await expect(page.getByText("e2e-rapor.txt")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("ready")).toBeVisible({ timeout: 30_000 });

  await page.getByRole("link", { name: /AI Araçları|AI Tools/ }).first().click();
  await page.getByRole("button", { name: /Çalıştır|Run/ }).click();

  await expect(page.getByRole("heading", { name: /Sonuç|Result/ })).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByRole("button", { name: "PDF" })).toBeVisible();
});

test("paylaşım bağlantısı oluşturulur ve public sayfada açılır", async ({
  page,
  context,
}) => {
  const email = uniqueEmail("share");

  await page.goto("/register");
  await page.getByLabel(/E-?posta|Email/i).fill(email);
  await page.getByLabel(/Parola|Password/i).first().fill(PASSWORD);
  await page.getByRole("button", { name: /Kayıt|Register|Hesap/i }).click();
  await page.goto("/dashboard");

  await page.getByRole("link", { name: /Dokümanlar|Documents/ }).first().click();
  await page.setInputFiles('input[type="file"]', {
    name: "paylasim.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Paylasim testi icin ornek icerik."),
  });
  await expect(page.getByText("paylasim.txt")).toBeVisible({ timeout: 30_000 });

  await page.getByRole("button", { name: /Paylaş|Share/ }).first().click();
  await page.getByRole("button", { name: /Bağlantı oluştur|Create link/ }).click();

  const url = await page.getByText(/\/share\//).first().innerText();
  const token = url.trim().split("/share/")[1];

  const guest = await context.newPage();
  await guest.goto(`/share/${token}`);
  await expect(guest.getByText("paylasim.txt")).toBeVisible({ timeout: 20_000 });
});
