# FastAPI Translation API (mT5)

## Setup
```
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Example Request
POST /translate-text
{
  "text": "तिमीलाई कस्तो छ?",
  "source_lang": "ne"
}

मलाई लाग्थ्यो तिमीले मलाई राम्रो साथी ठानेर व्यवहार गर्छौ, तर तिम्रो व्यवहारले त्यसको विपरीत देखायो।
→ I thought you treated me as a good friend, but your actions showed the opposite.

यो प्रश्न सरल देखिए पनि यो वास्तवमा धेरै जटिल अवस्थाको मुख्य भाग हो।
→ Even though this question looks simple, it’s actually a major part of a very complex situation.

तिनीहरूले गरेका निर्णयले समाजका धेरै मानिसहरूको जीवन बदलिदिएको छ।
→ The decision they made has changed the lives of many people in society.

समय बित्दै जाँदा हामीले आफ्नै भावनाहरू बुझ्न गहिरोसँग सोच्नुपर्छ।
→ As time passes, we need to think deeply to understand our own emotions.




ඔබ මාව හොඳම මිතුරෙකු ලෙස සලකා බලනවා කියලා හිතුණා, නමුත් ඔබේ ක්‍රියා ඒකව වෙනස් කරලා දැක්වුණා.
→ I thought you considered me a good friend, but your actions showed otherwise.

මෙය සරළ ප්‍රශ්නයක් වගේ පේනත්, ඇත්ත වශයෙන්ම ඉතා සංකීර්ණ තත්වයක ප්‍රධාන කොටසක්.
→ Although this may seem like a simple question, it is actually a major part of a very complex situation.

ඔවුන් ගත් තීරණය සමාජයේ බොහෝ දෙනාගේ ජීවිත වෙනස් කරලා තියෙනවා.
→ The decision they made has changed the lives of many people in society.

කාලය ගෙවෙද්දි අපි අපේම හැඟීම් පවා පැහැදිලි කරගන්න කල්පනාවෙන් කතාවේම යොමු වෙන්න ඕනේ.
→ As time passes, even we need to reflect deeply to understand our own feelings.

අනෙක් අයගේ අදහස් අවමතාවයෙන් සලකා බලන වෙලාවක, ඒවා අපේ තීරණ වලට බලපාන හැටි අමතක කරන්න එපා.
→ When we consider others' opinions lightly, we must not forget how they can influence our decisions
