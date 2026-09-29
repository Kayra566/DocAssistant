# AI model dosyaları

`.gguf` uzantılı model dosyalarını bu klasöre bırakın. Uygulama otomatik olarak
görür; arayüzde **Panel → AI Modeli** sayfasında listelenir.

Kullanmak için:

1. Ollama'yı başlatın: `cd infra && docker compose --profile ai up -d ollama`
2. Arayüzde modelin yanındaki **İçe aktar** düğmesine basın.
3. **Kullan** ile aktif hale getirin — yeniden başlatma gerekmez.

Model dosyaları git'e eklenmez.
