using System;
using System.IO;
using System.Collections.Generic;
using BepInEx;
using BepInEx.IL2CPP;
using HarmonyLib;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace UniversalUnityTranslation
{
    [BepInPlugin("com.antigravity.universaltranslation", "Universal Unity Translation", "1.0.0")]
    public class Plugin : BasePlugin
    {
        public static BepInEx.Logging.ManualLogSource Log;
        private static Dictionary<string, string> translationDict = new Dictionary<string, string>();

        public override void Load()
        {
            Log = Log;
            Log.LogInfo("Universal Unity Translation Plugin Loaded!");

            LoadTranslations();

            var harmony = new Harmony("com.antigravity.universaltranslation");
            harmony.PatchAll();
        }

        private void LoadTranslations()
        {
            string transDir = Path.Combine(Paths.PluginPath, "translations");
            if (!Directory.Exists(transDir)) Directory.CreateDirectory(transDir);

            foreach (var file in Directory.GetFiles(transDir, "*.json"))
            {
                try
                {
                    string content = File.ReadAllText(file);
                    // Parse JSON key-values into translationDict
                    Log.LogInfo($"Loaded translation file: {Path.GetFileName(file)}");
                }
                catch (Exception ex)
                {
                    Log.LogError($"Error loading {file}: {ex.Message}");
                }
            }
        }

        public static bool TryTranslate(string orig, out string translated)
        {
            if (string.IsNullOrEmpty(orig))
            {
                translated = null;
                return false;
            }
            return translationDict.TryGetValue(orig, out translated);
        }

        // ==================== HARMONY HOOKS ====================

        [HarmonyPatch(typeof(TMP_Text), "set_text")]
        [HarmonyPrefix]
        public static void TMP_Text_SetText_Prefix(TMP_Text __instance, ref string value)
        {
            if (TryTranslate(value, out string trans))
            {
                value = trans;
            }
        }

        [HarmonyPatch(typeof(TextMeshProUGUI), "OnEnable")]
        [HarmonyPostfix]
        public static void TextMeshProUGUI_OnEnable_Postfix(TextMeshProUGUI __instance)
        {
            if (__instance != null && TryTranslate(__instance.text, out string trans))
            {
                __instance.text = trans;
            }
        }

        [HarmonyPatch(typeof(Text), "set_text")]
        [HarmonyPrefix]
        public static void Text_SetText_Prefix(Text __instance, ref string value)
        {
            if (TryTranslate(value, out string trans))
            {
                value = trans;
            }
        }
    }
}

