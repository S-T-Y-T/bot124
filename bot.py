import os
import sys
import logging
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.request import HTTPXRequest

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING,

# ════════════════════════════════════════════════════════════════
#  IN-MEMORY STORAGE
# ════════════════════════════════════════════════════════════════
STORAGE = {
    "users":    {},   # user_id -> {name, phone, username, joined}
    "results":  [],   # [{name, phone, lang, score, total, level, date}]
    "enrolled": [],   # [{name, phone, lang, level, date}]
}

# ════════════════════════════════════════════════════════════════
#  INGLIZ TILI — 40 ta savol
# ════════════════════════════════════════════════════════════════
EN_Q = [
    # A1 (1-8)
    {"lv":"Beginner (A1)",        "q":"1. What ___ your name?",                                                "o":[("A","is"),("B","are"),("C","am"),("D","be")],                             "a":"A"},
    {"lv":"Beginner (A1)",        "q":"2. I ___ a student.",                                                   "o":[("A","is"),("B","are"),("C","am"),("D","be")],                             "a":"C"},
    {"lv":"Beginner (A1)",        "q":"3. She ___ from London.",                                               "o":[("A","come"),("B","comes"),("C","coming"),("D","came")],                   "a":"B"},
    {"lv":"Beginner (A1)",        "q":"4. ___ you speak English?",                                             "o":[("A","Is"),("B","Are"),("C","Do"),("D","Does")],                           "a":"C"},
    {"lv":"Beginner (A1)",        "q":"5. There ___ a cat in the garden.",                                     "o":[("A","are"),("B","am"),("C","be"),("D","is")],                             "a":"D"},
    {"lv":"Beginner (A1)",        "q":"6. How ___ are you?",                                                   "o":[("A","older"),("B","old"),("C","oldest"),("D","age")],                     "a":"B"},
    {"lv":"Beginner (A1)",        "q":"7. I have ___ umbrella.",                                               "o":[("A","a"),("B","an"),("C","the"),("D","some")],                            "a":"B"},
    {"lv":"Beginner (A1)",        "q":"8. They ___ football on Saturdays.",                                    "o":[("A","plays"),("B","playing"),("C","play"),("D","is play")],               "a":"C"},
    # A2 (9-16)
    {"lv":"Elementary (A2)",      "q":"9. I ___ TV every evening.",                                            "o":[("A","watches"),("B","watching"),("C","watch"),("D","watched")],           "a":"C"},
    {"lv":"Elementary (A2)",      "q":"10. She ___ to school yesterday.",                                      "o":[("A","go"),("B","goes"),("C","going"),("D","went")],                       "a":"D"},
    {"lv":"Elementary (A2)",      "q":"11. ___ he ever been to Paris?",                                        "o":[("A","Have"),("B","Has"),("C","Did"),("D","Does")],                        "a":"B"},
    {"lv":"Elementary (A2)",      "q":"12. I can't find my keys. I think I ___ them.",                         "o":[("A","lose"),("B","lost"),("C","have lost"),("D","was losing")],           "a":"C"},
    {"lv":"Elementary (A2)",      "q":"13. What time ___ the train leave?",                                    "o":[("A","do"),("B","is"),("C","are"),("D","does")],                           "a":"D"},
    {"lv":"Elementary (A2)",      "q":"14. There aren't ___ eggs in the fridge.",                              "o":[("A","some"),("B","any"),("C","much"),("D","a")],                          "a":"B"},
    {"lv":"Elementary (A2)",      "q":"15. She has lived here ___ 2010.",                                      "o":[("A","for"),("B","since"),("C","during"),("D","from")],                    "a":"B"},
    {"lv":"Elementary (A2)",      "q":"16. He ___ never eaten sushi before.",                                  "o":[("A","is"),("B","was"),("C","has"),("D","have")],                          "a":"C"},
    # B1 (17-24)
    {"lv":"Pre-Intermediate (B1)","q":"17. If it rains tomorrow, we ___ stay at home.",                        "o":[("A","would"),("B","will"),("C","shall"),("D","should")],                  "a":"B"},
    {"lv":"Pre-Intermediate (B1)","q":"18. She ___ dinner when he called.",                                    "o":[("A","cooked"),("B","has cooked"),("C","was cooking"),("D","cooks")],      "a":"C"},
    {"lv":"Pre-Intermediate (B1)","q":"19. I wish I ___ fly like a bird.",                                     "o":[("A","can"),("B","will"),("C","could"),("D","would")],                     "a":"C"},
    {"lv":"Pre-Intermediate (B1)","q":"20. The Eiffel Tower ___ in Paris.",                                    "o":[("A","is located"),("B","locates"),("C","located"),("D","has located")],   "a":"A"},
    {"lv":"Pre-Intermediate (B1)","q":"21. By the time she arrived, we ___ already eaten.",                    "o":[("A","have"),("B","has"),("C","had"),("D","having")],                      "a":"C"},
    {"lv":"Pre-Intermediate (B1)","q":"22. He suggested ___ to the cinema.",                                   "o":[("A","go"),("B","to go"),("C","gone"),("D","going")],                      "a":"D"},
    {"lv":"Pre-Intermediate (B1)","q":"23. I'm looking forward ___ you soon.",                                 "o":[("A","to see"),("B","seeing"),("C","to seeing"),("D","see")],              "a":"C"},
    {"lv":"Pre-Intermediate (B1)","q":"24. The letter ___ by the secretary yesterday.",                        "o":[("A","typed"),("B","was typed"),("C","has typed"),("D","is typed")],       "a":"B"},
    # B2 (25-32)
    {"lv":"Intermediate (B2)",    "q":"25. ___ you rather have tea or coffee?",                                "o":[("A","Will"),("B","Do"),("C","Would"),("D","Should")],                     "a":"C"},
    {"lv":"Intermediate (B2)",    "q":"26. She must ___ very tired after such a long journey.",                 "o":[("A","been"),("B","being"),("C","to be"),("D","be")],                      "a":"D"},
    {"lv":"Intermediate (B2)",    "q":"27. Not only ___ he pass the exam, but he also got the highest score.", "o":[("A","does"),("B","has"),("C","did"),("D","had")],                         "a":"C"},
    {"lv":"Intermediate (B2)",    "q":"28. The report needs ___ before tomorrow.",                             "o":[("A","finish"),("B","finishing"),("C","to be finished"),("D","finished")], "a":"C"},
    {"lv":"Intermediate (B2)",    "q":"29. I'd rather you ___ tell anyone about this.",                        "o":[("A","don't"),("B","won't"),("C","wouldn't"),("D","didn't")],              "a":"D"},
    {"lv":"Intermediate (B2)",    "q":"30. ___ he works very hard, he never seems to succeed.",                "o":[("A","Despite"),("B","Although"),("C","However"),("D","Nevertheless")],    "a":"B"},
    {"lv":"Intermediate (B2)",    "q":"31. She ___ have told me earlier — I would have helped.",               "o":[("A","should"),("B","could"),("C","might"),("D","must")],                  "a":"A"},
    {"lv":"Intermediate (B2)",    "q":"32. Hardly ___ sat down when the phone rang.",                          "o":[("A","I had"),("B","had I"),("C","I have"),("D","have I")],                "a":"B"},
    # C1 (33-40)
    {"lv":"Upper Intermediate (C1)","q":"33. The suspect is said ___ the country.",                            "o":[("A","having fled"),("B","to flee"),("C","to have fled"),("D","fled")],    "a":"C"},
    {"lv":"Upper Intermediate (C1)","q":"34. No sooner ___ he arrived than the problems started.",             "o":[("A","has"),("B","did"),("C","was"),("D","had")],                          "a":"D"},
    {"lv":"Upper Intermediate (C1)","q":"35. It's high time we ___ a decision.",                               "o":[("A","make"),("B","have made"),("C","made"),("D","making")],               "a":"C"},
    {"lv":"Upper Intermediate (C1)","q":"36. She talked as though she ___ everything.",                        "o":[("A","knows"),("B","knew"),("C","has known"),("D","will know")],           "a":"B"},
    {"lv":"Upper Intermediate (C1)","q":"37. ___ for the fact that it rained, the party would have been perfect.","o":[("A","Apart"),("B","Except"),("C","But"),("D","Without")],            "a":"C"},
    {"lv":"Upper Intermediate (C1)","q":"38. The decision has been met with ___ opposition from the public.",  "o":[("A","wide"),("B","broad"),("C","large"),("D","widespread")],              "a":"D"},
    {"lv":"Upper Intermediate (C1)","q":"39. The policy is intended to ___ corruption in public institutions.","o":[("A","eradicate"),("B","erase"),("C","remove"),("D","delete")],           "a":"A"},
    {"lv":"Upper Intermediate (C1)","q":"40. ___ the economic downturn, the company posted record profits.",   "o":[("A","In spite"),("B","Despite of"),("C","Notwithstanding"),("D","Even")], "a":"C"},
]

# ════════════════════════════════════════════════════════════════
#  TURK TILI — 28 ta savol (A1:8, A2:10, B1:10)
# ════════════════════════════════════════════════════════════════
TR_Q = [
    # A1 (1-8) — Varaq A1
    {"lv":"Başlangıç (A1)", "q":"1. Mustafa, eve gel…… …………… markete uğradı.\nA) -dikten sonra  B) -maden önce  C) -meden önce  D) -dıktan sonra", "o":[("A","-dikten sonra"),("B","-maden önce"),("C","-meden önce"),("D","-dıktan sonra")], "a":"B"},
    {"lv":"Başlangıç (A1)", "q":"2. Kapıyı kapat…………… ……………………… içeriden kilitledi.\nA) -dıktan sonra  B) -dikten sonra  C) -tikten sonra  D) -tıktan sonra", "o":[("A","-dıktan sonra"),("B","-dikten sonra"),("C","-tikten sonra"),("D","-tıktan sonra")], "a":"A"},
    {"lv":"Başlangıç (A1)", "q":"3. Paragraftaki boşlukları doldurunuz (3 ta bo'sh joy):\nA) -madan önce / -dıktan sonra / -meden önce\nB) -meden önce / -duktan sonra / -meden önce\nC) -meden önce / -tuktan sonra / -meden önce\nD) -meden önce / -duktan sonra / -dikten sonra", "o":[("A","-madan önce / -dıktan sonra / -meden önce"),("B","-meden önce / -duktan sonra / -meden önce"),("C","-meden önce / -tuktan sonra / -meden önce"),("D","-meden önce / -duktan sonra / -dikten sonra")], "a":"B"},
    {"lv":"Başlangıç (A1)", "q":"4. Hangi cümlenin anlamı bozuktur?\nA) Okula gitmeden önce kırtasiyeye uğradı ve kalem aldı.\nB) Biraz televizyon izledikten sonra yattı.\nC) Eve gelmeden önce komşusuna uğradı.\nD) Eve girdikten sonra komşusuna uğradı.", "o":[("A","Okula gitmeden önce kırtasiyeye uğradı."),("B","Biraz televizyon izledikten sonra yattı."),("C","Eve gelmeden önce komşusuna uğradı."),("D","Eve girdikten sonra komşusuna uğradı.")], "a":"D"},
    {"lv":"Başlangıç (A1)", "q":"5. \"İki yıl Ankara'da oku ………\"\nA) -mış  B) -muş  C) -miş  D) -müş", "o":[("A","-mış"),("B","-muş"),("C","-miş"),("D","-müş")], "a":"C"},
    {"lv":"Başlangıç (A1)", "q":"6. Diyalogdaki boşluğa hangisi uygun?\n«Türkçe sınavına da gir ………»\nA) –memiş  B) –medi  C) –di  D) –miş", "o":[("A","–memiş"),("B","–medi"),("C","–di"),("D","–miş")], "a":"A"},
    {"lv":"Başlangıç (A1)", "q":"7. Hangisinde bir haberi başkasından öğrenme vardır?\nA) Dün akşam otobanda büyük bir kaza oldu.\nB) Haftaya hep birlikte Türkiye'ye gidecekler.\nC) Arkadaşım şiir okuma yarışmasında birinci olmuş.\nD) Ahmet, dün akşam babasıyla maça gitti.", "o":[("A","Dün akşam otobanda büyük bir kaza oldu."),("B","Haftaya hep birlikte Türkiye'ye gidecekler."),("C","Arkadaşım şiir okuma yarışmasında birinci olmuş."),("D","Ahmet, dün akşam babasıyla maça gitti.")], "a":"C"},
    {"lv":"Başlangıç (A1)", "q":"8. Cümleleri uygun sıralayınız:\n(1)Hangi maça? (2)Bütün gün… (3)Ne dersin… (4)Galatasaray-Fenerbahçe… (5)Senin haberin yok mu?.. (6)Kim söyledi?\nA) 3-1-4-5-2-6  B) 3-1-4-5-6-2  C) 1-2-4-3-6-5  D) 3-1-2-6-4-5", "o":[("A","3-1-4-5-2-6"),("B","3-1-4-5-6-2"),("C","1-2-4-3-6-5"),("D","3-1-2-6-4-5")], "a":"B"},
    # A2 (9-18) — Varaq A2
    {"lv":"Temel (A2)", "q":"9. Her gün odamı ………… bıktım.\nA) toplamaktan  B) toplamayı  C) toplamaya  D) toplamakta", "o":[("A","toplamaktan"),("B","toplamayı"),("C","toplamaya"),("D","toplamakta")], "a":"A"},
    {"lv":"Temel (A2)", "q":"10. Yağmurda ………… çok severiz.\nA) yürümekten  B) yürümeyi  C) yürümeye  D) yürümekte", "o":[("A","yürümekten"),("B","yürümeyi"),("C","yürümeye"),("D","yürümekte")], "a":"B"},
    {"lv":"Temel (A2)", "q":"11. Beni okulda, ………… kapısının önünde bekleyeceksin.\nA) giriş  B) iniş  C) duruş  D) varış", "o":[("A","giriş"),("B","iniş"),("C","duruş"),("D","varış")], "a":"D"},
    {"lv":"Temel (A2)", "q":"12. Japonca ………… karar verdim.\nA) öğrenmekten  B) öğrenmeyi  C) öğrenmeye  D) öğrenmekte", "o":[("A","öğrenmekten"),("B","öğrenmeyi"),("C","öğrenmeye"),("D","öğrenmekte")], "a":"C"},
    {"lv":"Temel (A2)", "q":"13. Siz, çay ………… hoşlanmıyor musunuz?\nA) içmekten  B) içmeyi  C) içmeye  D) içmekte", "o":[("A","içmekten"),("B","içmeyi"),("C","içmeye"),("D","içmekte")], "a":"A"},
    {"lv":"Temel (A2)", "q":"14. Öğrenciler, hafta sonunda piknik ………… düşünüyorlar.\nA) yapmaktan  B) yapmayı  C) yapmaya  D) yapmakta", "o":[("A","yapmaktan"),("B","yapmayı"),("C","yapmaya"),("D","yapmakta")], "a":"B"},
    {"lv":"Temel (A2)", "q":"15. Ampul, Edison'un …………\nA) yarışıdır  B) bitişidir  C) duruşudur  D) buluşudur", "o":[("A","yarışıdır"),("B","bitişidir"),("C","duruşudur"),("D","buluşudur")], "a":"D"},
    {"lv":"Temel (A2)", "q":"16. Bu kitabı ………… henüz başlamadım.\nA) okumaktan  B) okumayı  C) okumaya  D) okumakta", "o":[("A","okumaktan"),("B","okumayı"),("C","okumaya"),("D","okumakta")], "a":"C"},
    {"lv":"Temel (A2)", "q":"17. Bu yolun ………… yok.\nA) dönüşü  B) bakışı  C) duruşu  D) binişi", "o":[("A","dönüşü"),("B","bakışı"),("C","duruşu"),("D","binişi")], "a":"A"},
    {"lv":"Temel (A2)", "q":"18. Kitaplarını üniversitenin kütüphanesine ………… planlıyor.\nA) bağışlamaktan  B) bağışlamayı  C) bağışlamaya  D) bağışlamakta", "o":[("A","bağışlamaktan"),("B","bağışlamayı"),("C","bağışlamaya"),("D","bağışlamakta")], "a":"B"},
    # B1 (19-28) — Varaq B1
    {"lv":"Orta Öncesi (B1)", "q":"19. Lütfen hesabı ………………………?\nA) getirecek misiniz?  B) getirir misiniz?  C) getiriyor musunuz?  D) getirdiniz mi?", "o":[("A","getirecek misiniz?"),("B","getirir misiniz?"),("C","getiriyor musunuz?"),("D","getirdiniz mi?")], "a":"C"},
    {"lv":"Orta Öncesi (B1)", "q":"20. Bu pantolonu çok beğendim, ………………………?\nA) deniyor muyum?  B) denemiş miyim?  C) deneyebilir miyim?  D) denedim mi?", "o":[("A","deniyor muyum?"),("B","denemiş miyim?"),("C","deneyebilir miyim?"),("D","denedim mi?")], "a":"C"},
    {"lv":"Orta Öncesi (B1)", "q":"21. Pazara, yanıma para ………………………… gitmişim. Bu yüzden alışveriş yapamadım.\nA) alıp  B) ala ala  C) almadan  D) alarak", "o":[("A","alıp"),("B","ala ala"),("C","almadan"),("D","alarak")], "a":"C"},
    {"lv":"Orta Öncesi (B1)", "q":"22. Otobüse ………………………… Antalya'ya gittiler.\nA) binip  B) bindi  C) bine bine  D) binmiş", "o":[("A","binip"),("B","bindi"),("C","bine bine"),("D","binmiş")], "a":"A"},
    {"lv":"Orta Öncesi (B1)", "q":"23. Annem, zeytinyağlı yaprak ………………………… yapmış.\nA) sarması  B) kızartması  C) kavurması  D) haşlaması", "o":[("A","sarması"),("B","kızartması"),("C","kavurması"),("D","haşlaması")], "a":"A"},
    {"lv":"Orta Öncesi (B1)", "q":"24. Duraktaki adamın ………………………… hepimizi korkutuyor.\nA) bakması  B) bakışı  C) bakmadan  D) bakıp", "o":[("A","bakması"),("B","bakışı"),("C","bakmadan"),("D","bakıp")], "a":"B"},
    {"lv":"Orta Öncesi (B1)", "q":"25. Araba ………………………… sevmiyorum.\nA) kullanmayı  B) kullanmaya  C) kullanmakta  D) kullanmaktan", "o":[("A","kullanmayı"),("B","kullanmaya"),("C","kullanmakta"),("D","kullanmaktan")], "a":"D"},
    {"lv":"Orta Öncesi (B1)", "q":"26. Annem gömleğimi yıkamış, gömleğim kar ………………………… olmuş.\nA) kadar  B) daha  C) ve  D) gibi", "o":[("A","kadar"),("B","daha"),("C","ve"),("D","gibi")], "a":"D"},
    {"lv":"Orta Öncesi (B1)", "q":"27. Ben de en az senin ………………………… üzgünüm.\nA) kadar  B) daha  C) ve  D) gibi", "o":[("A","kadar"),("B","daha"),("C","ve"),("D","gibi")], "a":"A"},
    {"lv":"Orta Öncesi (B1)", "q":"28. ………………………… Türk mutfağı çok lezzetli.\nA) Onlara göre  B) Onlarca  C) Onun kadar  D) Onlar kadar", "o":[("A","Onlara göre"),("B","Onlarca"),("C","Onun kadar"),("D","Onlar kadar")], "a":"A"},
]

# ════════════════════════════════════════════════════════════════
#  ARAB TILI — 50 ta savol (A0:10, A1:10, A2:10, B1:10, B2:10)
# ════════════════════════════════════════════════════════════════
AR_Q = [
    # A0 (1-10)
    {"lv":"مبتدئ مطلق (A0)", "q":"1. اَنا ___ في البَيْتِ.", "o":[("A","أَسْكُنُ"),("B","كِتابٌ"),("C","جَميلٌ")], "a":"A"},
    {"lv":"مبتدئ مطلق (A0)", "q":"2. هٰذا ___ كَبيرٌ.", "o":[("A","بِنْتٌ"),("B","بَيْتٌ"),("C","تَذْهَبُ")], "a":"B"},
    {"lv":"مبتدئ مطلق (A0)", "q":"3. أَنا ___ الماءَ.", "o":[("A","أَشْرَبُ"),("B","طَويلٌ"),("C","سَيّارَةٌ")], "a":"A"},
    {"lv":"مبتدئ مطلق (A0)", "q":"4. ___ أَنْتَ يا أَحْمَدُ؟", "o":[("A","مَن"),("B","أَيْنَ"),("C","كَيْفَ")], "a":"A"},
    {"lv":"مبتدئ مطلق (A0)", "q":"5. أُحِبُّ ___ العَرَبِيَّةَ.", "o":[("A","اللُّغَةَ"),("B","يَكْتُبُ"),("C","بابٌ")], "a":"A"},
    {"lv":"مبتدئ مطلق (A0)", "q":"6. الطّالِبُ ___ الدَّرْسَ.", "o":[("A","يَقْرَأُ"),("B","قَلَمٌ"),("C","صَغيرٌ")], "a":"A"},
    {"lv":"مبتدئ مطلق (A0)", "q":"7. هِيَ ___ إِلَى المَدْرَسَةِ.", "o":[("A","تَذْهَبُ"),("B","كِتابٌ"),("C","جَديدٌ")], "a":"A"},
    {"lv":"مبتدئ مطلق (A0)", "q":"8. عِندي ___ أَحْمَرُ.", "o":[("A","يُصَلِّي"),("B","قَلَمٌ"),("C","يَأْكُلُ")], "a":"B"},
    {"lv":"مبتدئ مطلق (A0)", "q":"9. ___ القِطَّةُ تَحْتَ الكُرْسِيِّ.", "o":[("A","هٰذِهِ"),("B","هٰذا"),("C","هُمْ")], "a":"A"},
    {"lv":"مبتدئ مطلق (A0)", "q":"10. نَحْنُ ___ في الفَصْلِ.", "o":[("A","نَجْلِسُ"),("B","بَيْتٌ"),("C","سَريعٌ")], "a":"A"},
    # A1 (11-20)
    {"lv":"مبتدئ (A1)", "q":"11. أَبي ___ في المُسْتَشْفَى.", "o":[("A","يَعْمَلُ"),("B","كُرْسِيٌّ"),("C","جَميلَةٌ")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"12. مَتى ___ مِنَ المَدْرَسَةِ؟", "o":[("A","تَرْجِعُ"),("B","بَيْتٌ"),("C","طَويلٌ")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"13. نَحْنُ ___ كُرَةَ القَدَمِ كُلَّ يَوْمٍ.", "o":[("A","نَلْعَبُ"),("B","سَيّارَةٌ"),("C","جَديدٌ")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"14. أُخْتي تُحِبُّ ___ الكُتُبِ.", "o":[("A","قِراءَةَ"),("B","يَكْتُبُ"),("C","طَعامٌ")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"15. أَيْنَ ___ الآنَ؟", "o":[("A","أَنْتَ"),("B","ذَهَبَ"),("C","بَيْتٌ")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"16. المُعَلِّمُ ___ الدَّرْسَ جَيِّدًا.", "o":[("A","يَشْرَحُ"),("B","نَافِذَةٌ"),("C","سَريعٌ")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"17. أَنا أَذْهَبُ إِلَى السُّوقِ ___ أُمِّي.", "o":[("A","مَعَ"),("B","في"),("C","إِلى")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"18. ___ عِنْدَكَ أَخٌ؟", "o":[("A","هَلْ"),("B","ماذا"),("C","كَيْفَ")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"19. الوَلَدُ ___ التُّفّاحَةَ.", "o":[("A","يَأْكُلُ"),("B","كَبيرةٌ"),("C","مَدْرَسَةٌ")], "a":"A"},
    {"lv":"مبتدئ (A1)", "q":"20. القِطَّةُ ___ السَّريرِ.", "o":[("A","تَحْتَ"),("B","مِنْ"),("C","إِلى")], "a":"A"},
    # A2 (21-30)
    {"lv":"أساسي (A2)", "q":"21. ذَهَبْتُ إِلَى المَدْرَسَةِ ___ الحافِلَةِ.", "o":[("A","بِ"),("B","عَنْ"),("C","عَلَى")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"22. أُريدُ أَنْ ___ اللُّغَةَ العَرَبِيَّةَ.", "o":[("A","أَتَعَلَّمَ"),("B","مَكْتَبٌ"),("C","سَريعٌ")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"23. كانَ الجَوُّ ___ أَمْسِ.", "o":[("A","جَميلًا"),("B","يَكْتُبُ"),("C","طاوِلَةٌ")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"24. أَخي أَكْبَرُ ___ أُخْتي.", "o":[("A","مِنْ"),("B","إِلى"),("C","في")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"25. لَمْ ___ الطّالِبُ الوَاجِبَ.", "o":[("A","يَكْتُبْ"),("B","يَكْتُبُ"),("C","كَتَبَ")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"26. كَمْ ساعَةً ___ كُلَّ يَوْمٍ؟", "o":[("A","تَدْرُسُ"),("B","دِراسَةٌ"),("C","كَبيرٌ")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"27. أُفَضِّلُ الشّايَ ___ القَهْوَةِ.", "o":[("A","عَلَى"),("B","مِنْ"),("C","إِلى")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"28. الطالِبَتانِ ___ في الفَصْلِ.", "o":[("A","تَجْلِسانِ"),("B","يَجْلِسُ"),("C","جالِسٌ")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"29. هٰذا الكِتابُ ___ جِدًّا.", "o":[("A","مُفيدٌ"),("B","يَذْهَبُ"),("C","مَدينَةٌ")], "a":"A"},
    {"lv":"أساسي (A2)", "q":"30. إِذا دَرَسْتَ جَيِّدًا ___.", "o":[("A","تَنْجَحْ"),("B","نَجاحٌ"),("C","ناجِحٌ")], "a":"A"},
    # B1 (31-40)
    {"lv":"متوسط أدنى (B1)", "q":"31. لَوْ كانَ عِنْدي وَقْتٌ، ___ مَعَكُمْ.", "o":[("A","لَسافَرْتُ"),("B","أُسافِرُ"),("C","سَفَرٌ")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"32. الطالِبُ الَّذي ___ هُناكَ مُجْتَهِدٌ.", "o":[("A","يَجْلِسُ"),("B","جُلوسٌ"),("C","جالِسًا")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"33. يَجِبُ أَنْ ___ المُعَلِّمَ.", "o":[("A","نَحْتَرِمَ"),("B","اِحْتِرامٌ"),("C","مُحْتَرَمٌ")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"34. لَمّا ___ المَطَرُ، بَقِينا في البَيْتِ.", "o":[("A","نَزَلَ"),("B","يَنْزِلُ"),("C","مَطَرٌ")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"35. أُحِبُّ الأَشْخاصَ ___ يَقُولونَ الحَقَّ.", "o":[("A","الَّذينَ"),("B","الَّتي"),("C","الَّذي")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"36. هٰذِهِ المَدينَةُ أَجْمَلُ ___ تِلْكَ.", "o":[("A","مِنْ"),("B","في"),("C","إِلى")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"37. ما زِلْتُ ___ هٰذا الكِتابَ.", "o":[("A","أَقْرَأُ"),("B","قِراءَةٌ"),("C","مَقْروءٌ")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"38. يَتَعَلَّمُ الأَطْفالُ اللُّغاتِ ___.", "o":[("A","بِسُهولَةٍ"),("B","سَهْلٌ"),("C","أَسْهَلُ")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"39. سَأَذْهَبُ إِلَيْكَ ___ أَنْتَهِي مِنْ عَمَلي.", "o":[("A","بَعْدَ أَنْ"),("B","لِأَنَّ"),("C","رُبَّما")], "a":"A"},
    {"lv":"متوسط أدنى (B1)", "q":"40. الرَّجُلُ ___ في المَسْجِدِ إِمامٌ.", "o":[("A","الَّذي يُصَلِّي"),("B","صَلاةٌ"),("C","مُصَلًّى")], "a":"A"},
    # B2 (41-50)
    {"lv":"متوسط (B2)", "q":"41. رَغْمَ أَنَّ الطَّريقَ كانَ طَويلًا، ___ مُبَكِّرًا.", "o":[("A","وَصَلْنا"),("B","نَصِلُ"),("C","واصِلٌ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"42. أَتَمَنّى أَنْ ___ هٰذا المَشْروعَ بِالنَّجاحِ.", "o":[("A","نُنْهِيَ"),("B","إِنْهاءٌ"),("C","مُنْتَهٍ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"43. إِذا لَمْ تَهْتَمَّ بِصِحَّتِكَ، ___.", "o":[("A","سَتَمْرَضُ"),("B","مَريضٌ"),("C","مَرَضٌ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"44. كانَ الطّالِبُ يَتَكَلَّمُ ___ أَمامَ الجَميعِ.", "o":[("A","بِثِقَةٍ"),("B","واثِقٌ"),("C","ثِقَةٌ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"45. كُلَّما ___ في العُمْرِ، ازْدادَتْ خِبْرَتُهُ.", "o":[("A","تَقَدَّمَ"),("B","يَتَقَدَّمُ"),("C","تَقَدُّمٌ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"46. لا أَعْتَقِدُ أَنَّ هٰذا الرَّأْيَ ___.", "o":[("A","صَحيحٌ"),("B","يَصِحُّ"),("C","صِحَّةٌ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"47. يَحْتاجُ المُجْتَمَعُ إِلى أَشْخاصٍ ___.", "o":[("A","مُخْلِصينَ"),("B","إِخْلاصٌ"),("C","أَخْلَصَ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"48. بَعْدَما ___ الدَّرْسَ، خَرَجَ الطُّلّابُ.", "o":[("A","انْتَهى"),("B","يَنْتَهي"),("C","انْتِهاءٌ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"49. مِنَ المُهِمِّ أَنْ ___ الإِنْسانُ أَهْدافَهُ.", "o":[("A","يُحَدِّدَ"),("B","تَحْديدٌ"),("C","مُحَدَّدٌ")], "a":"A"},
    {"lv":"متوسط (B2)", "q":"50. لَوْ دَرَسْتَ أَكْثَرَ، ___ النَّتيجَةُ أَفْضَلَ.", "o":[("A","لَكانَتْ"),("B","تَكونُ"),("C","كائِنَةٌ")], "a":"A"},
]

ALL_QUESTIONS = {"english": EN_Q, "turkish": TR_Q, "arabic": AR_Q}

LEVEL_NAMES = {
    "english": ["Beginner (A1)","Elementary (A2)","Pre-Intermediate (B1)","Intermediate (B2)","Upper Intermediate (C1)"],
    "turkish": ["Başlangıç (A1)","Temel (A2)","Orta Öncesi (B1)","Orta (B2)","İleri (C1)"],
    "arabic":  ["مبتدئ مطلق (A0)","مبتدئ (A1)","أساسي (A2)","متوسط أدنى (B1)","متوسط (B2)"],
}
EMOJIS     = ["🔴","🟠","🟡","🟢","🔵"]
LANG_LABEL = {"english":"🇬🇧 Ingliz tili","turkish":"🇹🇷 Turk tili","arabic":"🇸🇦 Arab tili"}

# ════════════════════════════════════════════════════════════════
#  KURS MA'LUMOTLARI
# ════════════════════════════════════════════════════════════════
COURSE_INFO = {
    "english": (
        "🇬🇧 <b>Ingliz tili kurslari — Career Center</b>\n\n"
        "🔴 <b>A1 — Boshlang'ich</b>\n└ 3 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟠 <b>A2 — Asosiy</b>\n└ 3 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟡 <b>B1 — O'rta quyi</b>\n└ 4 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟢 <b>B2 — O'rta</b>\n└ 4 oy | Haftada 3 kun | 2 soat/dars\n\n"
        "🔵 <b>C1 — Yuqori</b>\n└ 5 oy | Haftada 3 kun | 2 soat/dars\n\n"
        "✅ Sertifikat • Tajribali o'qituvchilar • Zamonaviy darsliklar\n"
        "📞 Ro'yxatdan o'tish uchun Career Center bilan bog'laning!"
    ),
    "turkish": (
        "🇹🇷 <b>Turk tili kurslari — Career Center</b>\n\n"
        "🔴 <b>A1 — Başlangıç</b>\n└ 3 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟠 <b>A2 — Temel</b>\n└ 3 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟡 <b>B1 — Orta Öncesi</b>\n└ 4 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟢 <b>B2 — Orta</b>\n└ 4 oy | Haftada 3 kun | 2 soat/dars\n\n"
        "🔵 <b>C1 — İleri</b>\n└ 5 oy | Haftada 3 kun | 2 soat/dars\n\n"
        "✅ Sertifikat • Tajribali o'qituvchilar • Zamonaviy darsliklar\n"
        "📞 Ro'yxatdan o'tish uchun Career Center bilan bog'laning!"
    ),
    "arabic": (
        "🇸🇦 <b>Arab tili kurslari — Career Center</b>\n\n"
        "🔴 <b>A1 — مبتدئ</b>\n└ 3 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟠 <b>A2 — أساسي</b>\n└ 3 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟡 <b>B1 — متوسط أدنى</b>\n└ 4 oy | Haftada 3 kun | 1.5 soat/dars\n\n"
        "🟢 <b>B2 — متوسط</b>\n└ 4 oy | Haftada 3 kun | 2 soat/dars\n\n"
        "🔵 <b>C1 — متقدم</b>\n└ 5 oy | Haftada 3 kun | 2 soat/dars\n\n"
        "✅ Sertifikat • Tajribali o'qituvchilar • Zamonaviy darsliklar\n"
        "📞 Ro'yxatdan o'tish uchun Career Center bilan bog'laning!"
    ),
}

TEST_INTRO = {
    "english": (
        "🇬🇧 <b>Ingliz tili Placement Test</b>\n\n"
        "📝 40 ta savol | 5 daraja (har birida 8 ta):\n"
        "🔴 A1 (1-8)  🟠 A2 (9-16)  🟡 B1 (17-24)\n"
        "🟢 B2 (25-32)  🔵 C1 (33-40)\n\nOmad! 🍀"
    ),
    "turkish": (
        "🇹🇷 <b>Türkçe Placement Test</b>\n\n"
        "📝 28 ta savol | 3 daraja:\n"
        "🔴 A1 (1-8)  🟠 A2 (9-18)  🟡 B1 (19-28)\n\n"
        "Başarılar! 🍀"
    ),
    "arabic": (
        "🇸🇦 <b>اختبار تحديد المستوى — العربية</b>\n\n"
        "📝 50 ta savol | 5 daraja (har birida 10 ta):\n"
        "🔴 A0 (1-10)  🟠 A1 (11-20)  🟡 A2 (21-30)\n"
        "🟢 B1 (31-40)  🔵 B2 (41-50)\n\nحظاً موفقاً! 🍀"
    ),
}

# ════════════════════════════════════════════════════════════════
#  KLAVIATURALAR
# ════════════════════════════════════════════════════════════════
CONTACT_KB = ReplyKeyboardMarkup(
    [[KeyboardButton("📱 Telefon raqamimni ulashish", request_contact=True)]],
    resize_keyboard=True, one_time_keyboard=True,
)

MAIN_KB = ReplyKeyboardMarkup(
    [
        ["💬 Career Center haqida fikr bildirish"],
        ["📖 Kurslarimiz haqida ma'lumot", "📝 Placement Test"],
    ],
    resize_keyboard=True,
)

COURSE_LANG_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🇸🇦 Arab tili",   callback_data="course_arabic")],
    [InlineKeyboardButton("🇬🇧 Ingliz tili", callback_data="course_english")],
    [InlineKeyboardButton("🇹🇷 Turk tili",   callback_data="course_turkish")],
])

TEST_LANG_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🇸🇦 Arab tili",   callback_data="test_arabic")],
    [InlineKeyboardButton("🇬🇧 Ingliz tili", callback_data="test_english")],
    [InlineKeyboardButton("🇹🇷 Turk tili",   callback_data="test_turkish")],
])

def result_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Kursga yoziling", callback_data="enroll_course")],
        [InlineKeyboardButton("👨‍💼 Admin bilan bog'lanish", url=ADMIN_LINK)],
    ])

# ════════════════════════════════════════════════════════════════
#  YORDAMCHI FUNKSIYALAR
# ════════════════════════════════════════════════════════════════
LEVEL_THRESHOLDS = {
    "english": [7, 15, 23, 31],   # 40 savol uchun
    "turkish": [4, 11, 19, 24],   # 28 savol uchun
    "arabic":  [9, 19, 29, 39],   # 50 savol uchun (10 savol har darajada)
}

def get_level(score: int, lang: str) -> str:
    names      = LEVEL_NAMES.get(lang, LEVEL_NAMES["english"])
    thresholds = LEVEL_THRESHOLDS.get(lang, [7, 15, 23, 31])
    i = sum(1 for t in thresholds if score > t)
    return f"{EMOJIS[i]} {names[i]}"


def question_kb(q: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{l}) {t}", callback_data=f"ans_{l}")]
        for l, t in q["o"]
    ])


# ════════════════════════════════════════════════════════════════
#  HANDLERLAR
# ════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "👋 <b>Career Center botiga xush kelibsiz!</b>\n\n"
        "Davom etish uchun telefon raqamingizni ulashing 👇",
        parse_mode="HTML", reply_markup=CONTACT_KB,
    )


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    user    = update.effective_user
    name     = user.full_name or user.first_name
    phone    = contact.phone_number
    username = f"@{user.username}" if user.username else "—"
    context.user_data["phone"]    = phone
    context.user_data["name"]     = name
    context.user_data["user_id"]  = user.id
    context.user_data["username"] = username

    STORAGE["users"][user.id] = {
        "name": name, "phone": phone, "username": username,
        "joined": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    await update.message.reply_text(
        f"✅ <b>Ro'yxatdan o'tdingiz!</b>\n\nXush kelibsiz, <b>{user.first_name}</b>! 👋\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇",
        parse_mode="HTML", reply_markup=MAIN_KB,
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text

    if not context.user_data.get("phone"):
        await update.message.reply_text(
            "Iltimos, avval telefon raqamingizni ulashing 👇",
            reply_markup=CONTACT_KB,
        )
        return

    if text == "💬 Career Center haqida fikr bildirish":
        context.user_data["state"] = "awaiting_feedback"
        await update.message.reply_text(
            "✍️ <b>Fikringizni yozing!</b>\n\n"
            "Career Center haqidagi fikr-mulohazalaringizni yozing.\n"
            "Rahbarimizga avtomatik yuboriladi. 📩",
            parse_mode="HTML",
        )
        return

    if text == "📖 Kurslarimiz haqida ma'lumot":
        await update.message.reply_text(
            "📖 <b>Qaysi til kurslari haqida ma'lumot olmoqchisiz?</b>",
            parse_mode="HTML", reply_markup=COURSE_LANG_KB,
        )
        return

    if text == "📝 Placement Test":
        await update.message.reply_text(
            "📝 <b>Qaysi til bo'yicha test topshirmoqchisiz?</b>",
            parse_mode="HTML", reply_markup=TEST_LANG_KB,
        )
        return

    if context.user_data.get("state") == "awaiting_feedback":
        context.user_data["state"] = None
        lang      = context.user_data.get("test_lang")
        lang_name = LANG_LABEL.get(lang, "Test topshirilmagan")
        level     = context.user_data.get("result_level", "—")
        score     = context.user_data.get("result_score", "—")
        total     = context.user_data.get("result_total", "—")

        msg = (
            "📝 <b>Yangi fikr-mulohaza!</b>\n\n"
            f"👤 {context.user_data.get('name','?')} ({context.user_data.get('username','?')})\n"
            f"🆔 <code>{context.user_data.get('user_id','?')}</code>\n"
            f"📞 {context.user_data.get('phone','?')}\n"
            f"🌐 Test tili: {lang_name}\n"
            f"📊 Natija: {score}/{total} — {level}\n\n"
            f"💬 <b>Fikr:</b>\n{text}"
        )
        try:
            await context.bot.send_message(chat_id=MANAGER_ID, text=msg, parse_mode="HTML")
            await update.message.reply_text(
                "✅ <b>Rahmat!</b> Fikringiz rahbarimizga yuborildi. 🙏",
                parse_mode="HTML",
            )
        except Exception as e:
            logging.warning(f"Manager xato: {e}")
            await update.message.reply_text("⚠️ Xabar yuborishda xatolik yuz berdi.")


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data  = query.data

    if data.startswith("course_"):
        lang = data[7:]
        await query.message.reply_text(COURSE_INFO[lang], parse_mode="HTML")
        return

    if data.startswith("test_"):
        lang = data[5:]
        context.user_data.update({
            "test_lang": lang, "score": 0,
            "current": 0, "answers": [],
            "state": "in_test",
        })
        await query.message.reply_text(TEST_INTRO[lang], parse_mode="HTML")
        await send_q(query.message, context)
        return

    if data.startswith("ans_"):
        if context.user_data.get("state") != "in_test":
            return
        await process_ans(query, context)
        return

    if data == "enroll_course":
        lang_name = LANG_LABEL.get(context.user_data.get("test_lang", ""), "")
        level     = context.user_data.get("result_level", "—")
        STORAGE["enrolled"].append({
            "name":     context.user_data.get("name", "?"),
            "phone":    context.user_data.get("phone", "?"),
            "username": context.user_data.get("username", "—"),
            "lang":     lang_name, "level": level,
            "date":     datetime.now().strftime("%d.%m.%Y %H:%M"),
        })
        await query.message.reply_text(
            "✅ <b>Zo'r!</b> Ma'lumotlaringiz qabul qilindi.\n\n"
            f"Reception bilan bog'laning: {RECEPTION_LINK}",
            parse_mode="HTML",
        )
        return

    # ── Admin callbacklar ───────────────────────────────────────
    if data.startswith("adm_"):
        if str(query.from_user.id) != MANAGER_ID:
            return
        await handle_admin_cb(query, data)
        return


async def send_q(msg, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data["test_lang"]
    idx  = context.user_data["current"]
    qs   = ALL_QUESTIONS[lang]

    if idx >= len(qs):
        await show_result(msg, context)
        return

    q = qs[idx]
    header = f"<b>{q['lv']}</b>  |  {idx + 1}/{len(qs)}\n\n{q['q']}"
    await msg.reply_text(header, reply_markup=question_kb(q), parse_mode="HTML")


async def process_ans(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data["test_lang"]
    idx  = context.user_data["current"]
    qs   = ALL_QUESTIONS[lang]

    if idx >= len(qs):
        return

    q          = qs[idx]
    user_ans   = query.data.split("_")[1]
    correct    = q["a"]
    is_correct = user_ans == correct

    if is_correct:
        context.user_data["score"] += 1
        mark = "✅"
    else:
        ct   = next(t for l, t in q["o"] if l == correct)
        mark = f"❌  To'g'ri: <b>{correct}) {ct}</b>"

    try:
        await query.edit_message_text(f"{q['q']}\n\n{mark}", parse_mode="HTML")
    except Exception:
        pass

    context.user_data["current"] = idx + 1
    await send_q(query.message, context)


async def show_result(msg, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang      = context.user_data["test_lang"]
    score     = context.user_data["score"]
    total     = len(ALL_QUESTIONS[lang])
    level     = get_level(score, lang)
    lang_name = LANG_LABEL[lang]
    context.user_data.update({"result_level": level, "result_score": score,
                               "result_total": total, "state": None})

    STORAGE["results"].append({
        "name":  context.user_data.get("name", "?"),
        "phone": context.user_data.get("phone", "?"),
        "username": context.user_data.get("username", "—"),
        "lang":  lang_name, "score": score, "total": total, "level": level,
        "date":  datetime.now().strftime("%d.%m.%Y %H:%M"),
    })

    text = (
        f"🎉 <b>Tabriklaymiz!</b> Siz {lang_name} placement testni muvafaqiyatli topshirdingiz!\n\n"
        f"📊 <b>Sizning darajangiz:</b> {level}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Endi siz bilimingizni yanada mustahkamlash vaqti keldi!\n\n"
        "🏆 <b>CAREER CENTER</b> bilan guruhlarga hoziroq qo'shiling va bonuslarga ega bo'ling! 🎁"
    )
    await msg.reply_text(text, parse_mode="HTML", reply_markup=result_kb())


# ════════════════════════════════════════════════════════════════
#  ADMIN PANEL
# ════════════════════════════════════════════════════════════════
ADMIN_MAIN_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="adm_users"),
     InlineKeyboardButton("📊 Test natijalari",  callback_data="adm_results")],
    [InlineKeyboardButton("✅ Kursga yozilganlar", callback_data="adm_enrolled")],
])

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != MANAGER_ID:
        return
    u = len(STORAGE["users"])
    r = len(STORAGE["results"])
    e = len(STORAGE["enrolled"])
    await update.message.reply_text(
        "🔐 <b>ADMIN PANEL</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{u}</b>\n"
        f"📝 Placement test yechganlar: <b>{r}</b>\n"
        f"✅ Kursga yozilganlar: <b>{e}</b>",
        parse_mode="HTML", reply_markup=ADMIN_MAIN_KB,
    )


async def handle_admin_cb(query, data: str) -> None:
    if data == "adm_users":
        items = list(STORAGE["users"].values())
        if not items:
            await query.message.reply_text("Hali foydalanuvchilar yo'q.")
            return
        lines = [f"{i}. {u['name']} | {u['phone']} | {u['username']} | {u['joined']}"
                 for i, u in enumerate(items[-30:], 1)]
        await query.message.reply_text(
            f"👥 <b>Foydalanuvchilar ({len(items)} ta):</b>\n\n" + "\n".join(lines),
            parse_mode="HTML",
        )

    elif data == "adm_results":
        items = STORAGE["results"]
        if not items:
            await query.message.reply_text("Hali test natijalari yo'q.")
            return
        lines = []
        for i, r in enumerate(items[-20:], 1):
            lines.append(
                f"{i}. {r['name']} | {r['phone']}\n"
                f"   {r['lang']} | {r['score']}/{r['total']} | {r['level']}\n"
                f"   📅 {r['date']}"
            )
        await query.message.reply_text(
            f"📊 <b>Test natijalari ({len(items)} ta):</b>\n\n" + "\n\n".join(lines),
            parse_mode="HTML",
        )

    elif data == "adm_enrolled":
        items = STORAGE["enrolled"]
        if not items:
            await query.message.reply_text("Hali kursga yozilganlar yo'q.")
            return
        lines = []
        for i, e in enumerate(items[-20:], 1):
            lines.append(
                f"{i}. {e['name']} | {e['phone']}\n"
                f"   {e['lang']} | {e['level']}\n"
                f"   📅 {e['date']}"
            )
        await query.message.reply_text(
            f"✅ <b>Kursga yozilganlar ({len(items)} ta):</b>\n\n" + "\n\n".join(lines),
            parse_mode="HTML",
        )


# ════════════════════════════════════════════════════════════════
#  XATO HANDLER
# ════════════════════════════════════════════════════════════════
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    import telegram.error as tgerr
    if isinstance(context.error, (tgerr.TimedOut, tgerr.NetworkError)):
        return
    logging.error("Xato:", exc_info=context.error)


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════
def main() -> None:
    request = HTTPXRequest(
        connect_timeout=60,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=60,
    )
    app = Application.builder().token(TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(error_handler)
    print("✅ Bot ishga tushdi! Telegram'da /start bosing.")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        timeout=30,
    )


if __name__ == "__main__":
    main()
