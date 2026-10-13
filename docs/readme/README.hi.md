# OpenBacktesting

**Python में ऐतिहासिक बैकटेस्टिंग: रणनीति के नियमों से लेकर जाँचने योग्य नतीजों तक।**

[English](../../README.md) · [Español](README.es.md) · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · **हिन्दी**

हर कैंडल पर चलने वाली रणनीतियाँ लिखें, ऐतिहासिक बाज़ार डेटा पर उनका मूल्यांकन करें और ऑर्डर, ट्रेड, इक्विटी तथा जोखिम के आँकड़े जाँचें। OpenBacktesting एक स्वतंत्र Python पैकेज है, जिसमें इंडिकेटर, पैरामीटर ऑप्टिमाइज़ेशन, Portfolio रिपोर्ट और चार्ट के लिए डेटा एक्सपोर्ट शामिल हैं।

**Python 3.12–3.14** · **संस्करण 0.2.0** · वितरण और इम्पोर्ट का नाम: `openbacktesting`

[शुरुआत करें](#quick-start) · [मैनुअल](../core/index.md) · [उदाहरण](../../examples/README.md) · [समस्या बताएँ](https://github.com/lucidcog/openbacktesting/issues)

## प्रमुख प्रायोजक — Pineify

<a href="https://pineify.app">
  <img src="../assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app), OpenBacktesting का प्रमुख सशुल्क प्रायोजक है।** उसका आर्थिक सहयोग इस परियोजना के खर्चों में मदद करता है।

Pineify, AI की मदद से Pine Script कोड लिखने की सुविधा और TradingView इंडिकेटर व रणनीतियाँ बनाने के लिए एक विज़ुअल एडिटर देता है। [Pineify देखें →](https://pineify.app)

## आप क्या कर सकते हैं

- **रणनीतियाँ बनाएँ:** हर कैंडल पर चलने वाला जीवनचक्र, निश्चित प्रकार वाले इनपुट, बिल्ट-इन इंडिकेटर और साथ जोड़े जा सकने वाले सहायक फ़ंक्शन इस्तेमाल करें।
- **निष्पादन जाँचें:** ऑर्डर, फ़िल, पोज़िशन साइज़, शुल्क, बंद ट्रेड और खुले लॉट देखें।
- **नतीजों का विश्लेषण करें:** हर रन के लिए pandas आँकड़े, इक्विटी कर्व और अपरिवर्तनीय Portfolio रिपोर्ट पढ़ें।
- **पैरामीटर की तुलना करें:** ग्रिड सर्च या वैकल्पिक SAMBO ऑप्टिमाइज़ेशन चलाएँ, प्रयोगों के नतीजे सहेजें और अपने रेंडरर के लिए चार्ट डेटा एक्सपोर्ट करें।

<a name="quick-start"></a>

## शुरुआत करें

[uv](https://docs.astral.sh/uv/getting-started/installation/) इंस्टॉल करें और Python `>=3.12,<3.15` इस्तेमाल करें। टर्मिनल में चलाएँ:

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
uv sync --locked
uv run --locked python examples/advanced/run_author.py
```

यह उदाहरण पैकेज में शामिल GOOG के ऐतिहासिक डेटा का इस्तेमाल करता है; बाज़ार डेटा डाउनलोड करने की ज़रूरत नहीं है। यह रिटर्न, ट्रेड की संख्या, अधिकतम ड्रॉडाउन और नतीजों की तालिकाएँ दिखाता है। चरणों की व्याख्या के लिए [आपका पहला बैकटेस्ट](../core/quickstart.md) देखें।

वैकल्पिक रूप से, डाउनलोड किया हुआ सोर्स कोड किसी मौजूदा Python एनवायरनमेंट में इंस्टॉल करें:

```sh
python -m pip install .
```

मूल निर्भरताएँ NumPy, pandas और `pandas-ta-classic==0.8.32` हैं। SAMBO ऑप्टिमाइज़ेशन के लिए `python -m pip install '.[optimize]'` या `uv sync --locked --extra optimize` इस्तेमाल करें। ये सोर्स से इंस्टॉल करने के निर्देश हैं; इनमें PyPI पर रिलीज़ उपलब्ध होने की धारणा नहीं है। [बिल्ड और वितरण की जानकारी](../core/development.md)।

## न्यूनतम बैकटेस्ट

यह कोड रिपॉज़िटरी की रूट डायरेक्टरी में `quickstart.py` के नाम से सहेजें और `uv run --locked python quickstart.py` चलाएँ:

```python
from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


class BuyAndHold(Strategy):
    def init(self):
        pass

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=1)


result = Backtest(GOOG, BuyAndHold, end_policy="close_at_last_close").run()
print(result[["Return [%]", "# Trades", "Max. Drawdown [%]"]])
```

यह रणनीति पहली कैंडल पर एक यूनिट खरीदने का अनुरोध करती है। डिफ़ॉल्ट रूप से ऑर्डर अगली कैंडल के ओपन पर निष्पादित होता है; `close_at_last_close` बची हुई पोज़िशन को अंतिम क्लोज़ पर बंद करता है।

`run()` एक pandas Series लौटाता है। ट्रेड के लिए `result["_trades"]` और इक्विटी इतिहास के लिए `result["_equity_curve"]` इस्तेमाल करें। सभी फ़ील्ड और Portfolio एक्सपोर्ट के लिए [नतीजों की गाइड](../core/guides/results.md) देखें; अंडरस्कोर से शुरू होने वाले फ़ील्ड मूल डायग्नोस्टिक डेटा हैं, अलग-अलग भाषाओं के बीच डेटा आदान-प्रदान का स्थिर अनुबंध नहीं।

## दस्तावेज़

विस्तृत मैनुअल और उदाहरण फ़िलहाल अंग्रेज़ी में हैं।

| विषय | संदर्भ |
| --- | --- |
| शुरुआती कदम | [पहला बैकटेस्ट](../core/quickstart.md) · [उदाहरणों की सूची](../../examples/README.md) |
| रणनीतियाँ और डेटा | [रणनीति का जीवनचक्र](../core/guides/author.md) · [बाज़ार डेटा](../core/guides/data.md) · [मुख्य API](../core/reference/core.md) |
| इंडिकेटर | [इंडिकेटर सूची](../core/reference/indicators/index.md) |
| निष्पादन और ऑप्टिमाइज़ेशन | [रणनीतियाँ चलाएँ](../core/guides/runtime.md) · [पैरामीटर प्रयोग](../core/guides/optimizer.md) |
| नतीजे और चार्ट | [नतीजे और Portfolio](../core/guides/results.md) · [चार्ट डेटा एक्सपोर्ट](../core/guides/plotting.md) |
| डेवलपमेंट | [सत्यापन और बिल्ड](../core/development.md) · [मौजूदा सीमाएँ](../core/limitations.md) |

## दायरा और अनुकूलता

- ट्रेडिंग मॉडल में **एक एसेट और एक सेटलमेंट मुद्रा** होती है। Portfolio रिपोर्ट एक रन का विवरण देती है; यह कई एसेट वाला पोर्टफोलियो खाता नहीं है।
- पैकेज गणना और चार्ट डेटा देता है। इसमें **चार्ट रेंडरर, लाइव ट्रेडिंग इंजन, कोड सैंडबॉक्स या Pine Script कन्वर्टर शामिल नहीं हैं**, और यह Pine जैसे निष्पादन अर्थ की गारंटी नहीं देता। केवल भरोसेमंद रणनीति कोड चलाएँ।
- Windows समर्थन और Pine के साथ पूर्ण तुलना का सत्यापन नहीं हुआ है। निष्पादन और बाज़ार मॉडल की सीमाओं के लिए [मौजूदा सीमाएँ](../core/limitations.md) देखें।

वितरण और इम्पोर्ट, दोनों का नाम `openbacktesting` है; पुराने नामों वाले एंट्री पॉइंट नहीं हैं। पुराने मॉड्यूल पथ वाले pickle अपने-आप माइग्रेट नहीं होते, पुराने ब्रांड पहचानकर्ताओं वाले आर्काइव पढ़े जा सकने की गारंटी नहीं है और पुरानी निष्पादन पहचान वाले प्रयोग दोबारा चलाने होंगे। [माइग्रेशन और स्रोत की जानकारी](../core/development.md#provenance-and-behavioral-boundaries)।

## सहायता और योगदान

बग, सवाल और नई सुविधाओं के अनुरोध के लिए [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) इस्तेमाल करें। Python और पैकेज के संस्करण, समस्या दोहराने वाला न्यूनतम उदाहरण तथा अपेक्षित और वास्तविक व्यवहार शामिल करें। [Pull requests](https://github.com/lucidcog/openbacktesting/pulls) के ज़रिए योगदान का स्वागत है।

कोड में बदलाव प्रस्तावित करने से पहले चलाएँ:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

सभी जाँचों के लिए [डेवलपमेंट गाइड](../core/development.md) देखें। सार्वजनिक व्यवहार में बदलाव के साथ दस्तावेज़, चलने योग्य उदाहरण और उनके निष्पादन का सत्यापन ज़रूरी है। कोड, टिप्पणियाँ और तकनीकी दस्तावेज़ डिफ़ॉल्ट रूप से अंग्रेज़ी में हैं; README के अनुवाद जानबूझकर स्थानीयकृत सामग्री हैं।

## अनुवाद

[अंग्रेज़ी README](../../README.md) मूल संदर्भ है। स्पेनिश, ब्राज़ीली पुर्तगाली, फ़्रेंच, जर्मन, इतालवी और हिन्दी में अनुवाद उपलब्ध हैं। ऊपर दिए भाषा लिंक इस्तेमाल करें और बदलाव करते समय [अनुवाद गाइड](TRANSLATING.md) का पालन करें। कमांड, API पहचानकर्ता, कार्यक्षमता की सीमाएँ और प्रायोजक का उल्लेख सभी भाषाओं में एक-समान रखें।

## लाइसेंस और स्रोत

परियोजना का घोषित लाइसेंस [Apache-2.0](../../LICENSE) है। तीसरे पक्ष की सामग्री अपनी मूल लाइसेंस शर्तों के अधीन रहती है, जिसमें [इंडिकेटर संदर्भ डेटा](../../tests/fixtures/indicator_expansion/README.md) भी शामिल है।

[सोर्स मैनिफ़ेस्ट](../../source-manifest.json) में [AGPL-3.0 लाइसेंस वाले अपस्ट्रीम स्नैपशॉट](https://github.com/kernc/backtesting.py/blob/ca2e2611621e472542ba90f7243a1fa06a7d7108/LICENSE.md) से किए गए रूपांतरण दर्ज हैं। Apache-2.0 की घोषणा उन शर्तों की जगह नहीं लेती; व्युत्पन्न कोड को केवल Apache-2.0 के तहत वितरित करने के लिए अलग अनुमति चाहिए। [एक्सट्रैक्शन मैनिफ़ेस्ट](../../extraction-manifest.json) में सीधे स्रोत का स्नैपशॉट और पथों का मानचित्र दर्ज है।
