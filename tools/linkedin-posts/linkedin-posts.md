# LinkedIn Posts — OpenShift & Spring Boot series

Schedule: one post a week, same day as the blog post date (Tue/Wed, 9–11 AM KSA time works best).
Each post ends with the article link. Pair each with a visual card (title + 3–4 bullets) as in previous series.

---

## Post 1 — OpenShift is not just Kubernetes
Link: https://bhry98.github.io/blog/openshift-vs-kubernetes/

"OpenShift ده مجرد Kubernetes عليه لوجو Red Hat"

الجملة دي بسمعها كتير… وهي نصها صح بس 👇

أي OpenShift cluster هو Kubernetes كامل: الـ Deployments والـ Services والـ ConfigMaps بتشتغل زي ما هي.
الفرق في كل الحاجات اللي Red Hat قررت إنك مش محتاج تركّبها بإيدك:

🔹 Routes + HAProxy router جاهزين، تعمل expose لأي app بأمر واحد
🔹 Security by default، الـ containers مش بتشتغل root أصلاً
🔹 OAuth server داخلي، تربطه بـ LDAP أو Keycloak وخلاص
🔹 Image registry + ImageStreams + Builds جوه الـ cluster
🔹 Prometheus و Alertmanager متسطبين من الأول
🔹 Upgrade للـ cluster كله عن طريق Cluster Version Operator
🔹 OperatorHub: Kafka و Keycloak و Argo CD و Cloud Pak بكام click

يعني Kubernetes بيديك موتور… و OpenShift بيديك العربية كاملة 🚗

بس هل ده دايماً يستاهل؟ لأ.
في المقال كتبت مقارنة كاملة جدول بجدول، وإمتى أختار OpenShift وإمتى Kubernetes العادي (أو EKS/AKS/GKE) يكون كفاية 👇

🔗 https://bhry98.github.io/blog/openshift-vs-kubernetes/

#OpenShift #Kubernetes #RedHat #DevOps #PlatformEngineering #CloudNative

---

## Post 2 — Why your container fails on OpenShift
Link: https://bhry98.github.io/blog/openshift-scc-arbitrary-uid/

الـ image شغالة تمام على Docker ✅
شغالة على Kubernetes ✅
تنزلها على OpenShift… CrashLoopBackOff ❌

```
mkdir() "/var/cache/nginx/client_temp" failed (13: Permission denied)
```

أول حل هتلاقيه على النت:
oc adm policy add-scc-to-user anyuid -z default

وده غالباً أسوأ حل 🚫

السبب الحقيقي:
OpenShift بيشغّل كل pod بـ random UID (زي 1000680000) من range خاص بالـ project، وبيعمل drop لكل الـ capabilities.
يعني الـ user ده مش مالك أي حاجة جوه الـ image، ومش يقدر يعمل bind على port 80.

الحل الصح إنك تصلّح الـ image نفسها، مش إنك تضعّف الـ cluster:
1️⃣ أي folder الـ app بتكتب فيه: chgrp -R 0 و chmod -R g=u
2️⃣ اسمع على 8080 مش 80
3️⃣ USER رقمي non-root… ومن غير chown وقت التشغيل

ولو فعلاً محتاج SCC تاني؟ فيه طريقة آمنة باستخدام dedicated service account، وأمر بيقولك أنهي SCC هتقبل الـ pod بتاعك.

كتبت المقال كامل بـ Dockerfile جاهز، وإزاي تتعامل مع الـ volumes والـ apps اللي محتاجة username 👇

🔗 https://bhry98.github.io/blog/openshift-scc-arbitrary-uid/

#OpenShift #ContainerSecurity #Docker #Kubernetes #DevSecOps #RedHat

---

## Post 3 — OpenShift Routes & TLS
Link: https://bhry98.github.io/blog/openshift-routes-tls/

عمل Route على OpenShift بياخد أمر واحد.
بس القرار المهم فعلاً: الـ TLS هيخلص فين؟ 🔐

OpenShift بيديك 3 اختيارات:

🟢 Edge
الـ TLS بيخلص عند الـ router، والـ traffic للـ pod بيبقى HTTP.
بسيط، وبيدعم path routing و sticky sessions و X-Forwarded headers.

🟡 Passthrough
الـ TLS بيوصل لحد الـ pod، والـ router مش بيفك التشفير خالص (بيقرأ الـ SNI بس).
ده اختيارك لو محتاج mTLS والـ app لازم تشوف client certificate، زي integrations البنوك والـ partners.

🔵 Re-encrypt
بيفك عند الـ router وبيشفّر تاني للـ pod.
مميزات الـ Edge + تشفير جوه الـ cluster. ومع service serving certificates بيبقى تقريباً ببلاش.

⚠️ ولو بتستخدم Spring Boot ورا Edge route: من غير forward-headers-strategy الـ redirects بتاعتك هتطلع http://

في المقال:
✔️ الأوامر لكل نوع
✔️ جدول مقارنة كامل
✔️ Route ولا Ingress؟
✔️ إزاي تحل صفحة "Application is not available" في 4 أوامر

🔗 https://bhry98.github.io/blog/openshift-routes-tls/

#OpenShift #TLS #Security #Kubernetes #SpringBoot #RedHat

---

## Post 4 — Debugging pods with oc
Link: https://bhry98.github.io/blog/openshift-debugging-pods/

لما الـ pod يقع، OpenShift تقريباً دايماً بيقولك السبب.
الشطارة إنك تعرف تسأله السؤال الصح 🔍

دي الـ playbook اللي بمشي بيها:

📌 Pending ← oc describe pod + oc describe quota
📌 ImagePullBackOff ← اسم الـ image غلط أو pull secret ناقص
📌 CrashLoopBackOff ← oc logs --previous (مش oc logs!)
📌 OOMKilled / Exit 137 ← الـ memory limit، ولو Java راجع MaxRAMPercentage
📌 CreateContainerConfigError ← ConfigMap أو Secret مش موجود
📌 Running بس 0/1 Ready ← readiness probe

وأهم أمر في الصفحة كلها:
oc debug deployment/my-app

بيشغّل نسخة من الـ pod بنفس الـ image والـ env والـ volumes، بس بـ shell بدل الـ command. تقدر تشغّل الـ app بإيدك وتشوف بتقع ليه.

في المقال كمان:
🛠️ oc rsh و oc cp و port-forward للـ remote debugging
🛠️ oc debug node و crictl لمشاكل الـ nodes
🛠️ must-gather قبل ما تفتح support case
🛠️ Cheat sheet تحفظها عندك

🔗 https://bhry98.github.io/blog/openshift-debugging-pods/

#OpenShift #Troubleshooting #Kubernetes #DevOps #SRE #RedHat

---

## Post 5 — Building Spring Boot images for OpenShift
Link: https://bhry98.github.io/blog/spring-boot-openshift-builds/

عندك Spring Boot JAR وعايز تشغّله على OpenShift.
تبني الـ image إزاي؟ 🤔

فيه 4 طرق، وكلهم شغالين:

1️⃣ Dockerfile في الـ CI (GitLab مثلاً) ← push لـ Nexus/Quay ← oc set image
الأكثر portability، والـ cluster بيشغّل workloads بس.

2️⃣ Docker strategy جوه OpenShift
نفس الـ Dockerfile بس الـ build بيحصل في الـ cluster. مفيد لو مفيش registry برّه.

3️⃣ Source-to-Image (S2I)
من غير Dockerfile خالص. تدّي OpenShift الكود أو الـ JAR والـ UBI OpenJDK builder يتصرف، و Red Hat هي اللي بتصلّح الـ base image.

4️⃣ Jib
من غير Dockerfile ومن غير Docker daemon. layers ذكية: تغيير في الكود = push بكام KB بس ⚡

بختار إزاي؟
• عندك CI و registry ← Dockerfile أو Jib
• فريق صغير أو cluster disconnected ← S2I
• microservices كتير و builds كل شوية ← Jib

في المقال: الأوامر كاملة، pom.xml config لـ Jib، gitlab-ci.yml، وجدول مقارنة 👇

🔗 https://bhry98.github.io/blog/spring-boot-openshift-builds/

#SpringBoot #OpenShift #Java #DevOps #GitLab #CloudNative
