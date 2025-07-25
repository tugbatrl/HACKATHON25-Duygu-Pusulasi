const scenarios = {
  step1: {
    text: `Sabah uyandın. Yeni bir okul yılı başlıyor ve en iyi arkadaşın Ece ile buluşmak için sabırsızlanıyorsun. Kahvaltını yapıp hazırlanırken, aklında Ece ile konuşacağınız konular var. Okul servisine binmeden önce, annenin sana yardım etmek isteyip istemediğini sorarsın. Annen "Gerek yok, sen de artık büyüdün" der. Ne yaparsın?`,
    options: [
      { text: `"Peki o zaman" deyip hemen yola çıkarsın.`, value: "A" },
      { text: `"Belki bir dahaki sefere" diyerek gülümser ve yola çıkarsın.`, value: "B" },
      { text: `"O zaman kahvaltı masasındaki bardakları toplayayım" der ve annene yardım edersin.`, value: "C" }
    ],
    next_step: "step2"
  },
  step2: {
    text: `Okul servisiyle okula geldin ve Ece'yle buluştun. Sınıfa girdiğinizde, en arka sıraya oturdunuz. O sırada sınıfa yeni bir öğrenci girdi. Adı Ali. Biraz çekingen duruyor ve kimseyle konuşmuyor. Öğretmen, Ali'yi tek başına bir sıraya oturttu. Ali'nin yalnız olduğunu görüyorsun. Ece sana "Hadi teneffüste bahçeye çıkalım" der. Ne yaparsın?`,
    options: [
      { text: `"Önce şu yeni çocukla tanışalım" der ve Ali'ye gülümsersin.`, value: "A" },
      { text: `Ece'yle beraber bahçeye çıkarsınız, Ali'yi kendi haline bırakırsınız.`, value: "B" },
      { text: `Öğretmene gidip "Ali'nin yanına oturabilir miyim?" diye sorarsın.`, value: "C" }
    ],
    next_step: "step3"
  },
  step3: {
    text: `Öğle arası oldu ve sen sıranın başında Ece'yi kantinden bekliyorsun. O sırada sınıfın zorba çocuğu Can, yanına geldi. "Ne kadar da komik bir çanta, sen bunu nereden buldun?" dedi. Sınıftaki birkaç kişi de ona güldü. Can, seninle alay ederken, Ece de kantinden geliyordu. Göz göze geldiniz. Ne yaparsın?`,
    options: [
      { text: `"Bunun komik bir yanı yok, kimsenin eşyasıyla dalga geçemezsin" der ve Can'a karşı durursun.`, value: "A" },
      { text: `Can'ı duymazdan gelir, yere düşen kitaplarını toplar ve ağlamaklı bir şekilde Ece'ye sarılırsın.`, value: "B" },
      { text: `Can'a karşılık verir ve "Senin çantan daha kötü" diyerek tartışmaya girersin.`, value: "C" }
    ],
    next_step: "step4"
  },
  step4: {
    text: `Zil çaldı ve sınıfa girdiniz. Can ve arkadaşları, artık seninle değil, Ali ile uğraşmaya başladı. Her teneffüs Ali'nin eşyalarını saklıyor, onunla alay ediyorlardı. Son derste, Ali'nin sıranın altında ağladığını gördün. Ece, "Sence öğretmene söylemeli miyiz?" diye sordu. Ne yaparsın?`,
    options: [
      { text: `"Kesinlikle! Birinin yardım etmesi gerekiyor" der ve öğretmene gidersin.`, value: "A" },
      { text: `"Bize de zorbalık yapar diye korkuyorum" der ve kararsız kalırsın.`, value: "B" },
      { text: `Ali'nin yanına gidip onu teselli etmeye çalışır, sonra da durumu kendi aranızda çözmeye çalışırsınız.`, value: "C" }
    ],
    next_step: "end"
  },
  end: {
    text: `Senaryo tamamlandı! Şimdi raporunu oluşturuyoruz...`,
    options: [],
    next_step: "report"
  }
};


const scenarioText = document.getElementById("scenario-text");
const optionsContainer = document.getElementById("options-container");
const reportContainer = document.getElementById("report-container");
const teacherReport = document.getElementById("teacher-report-content");
const restartButton = document.getElementById("restart-button");



let currentStep = "step1"
let answers = [];


function showScenario(stepId){
  const step = scenarios[stepId];
  currentStep = stepId;

  scenarioText.textContent = step.text;
  optionsContainer.innerHTML = "";
  restartButton.style.display = "none";

  step.options.forEach(option => {
    const button = document.createElement("button");
    button.textContent = option.text;
    button.onclick = () => {
      answers.push({ step: stepId , choice: option.value});
      showScenario(step.next_step);
    };
    optionsContainer.appendChild(button);
  });

  if (stepId === "end") {
    scenarioText.textContent = step.text;
    optionsContainer.innerHTML = "";
    showReportPlaceholder();

    restartButton.style.display = "block";

  }
}

function showReportPlaceholder() {
  scenarioText.textContent = "Rapor hazırlanıyor...";
  optionsContainer.innerHTML = "";
  reportContainer.style.display = "block";
}

restartButton.onclick = () => {
  answers = [];
  currentStep = "step1"
  reportContainer.style.display = "none";
  showScenario(currentStep);
};

showScenario(currentStep);



