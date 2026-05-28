import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import zhCN from "./locales/zh-CN.json";
import en from "./locales/en.json";
import ja from "./locales/ja.json";

export type Locale = "zh-CN" | "en" | "ja";

export const LOCALE_LABELS: Record<Locale, string> = {
  "zh-CN": "简体中文",
  en: "English",
  ja: "日本語",
};

const saved = (localStorage.getItem("locale") ?? "zh-CN") as Locale;

i18n
  .use(initReactI18next)
  .init({
    resources: {
      "zh-CN": { translation: zhCN },
      en: { translation: en },
      ja: { translation: ja },
    },
    lng: saved,
    fallbackLng: "zh-CN",
    interpolation: { escapeValue: false },
  });

export function setLocale(locale: Locale) {
  i18n.changeLanguage(locale);
  localStorage.setItem("locale", locale);
}

export default i18n;
