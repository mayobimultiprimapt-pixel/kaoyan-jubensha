/* 政治 M1 · 欧洲三大工人运动
   沉浸式叙事脚本。每个 scene 有：
     bg    - 背景色/渐变类名（CSS 在 style.css 定义）
     name  - 说话者（留空=旁白）
     face  - 立绘 emoji / 头像 key
     pos   - left | right | center（立绘位置）
     text  - 对话文本（\n 换行）
     next  - 下一个场景 key（无 choices 时）
     choices - [{text, next, tag?}] 选项
     get   - 进入本场景时给玩家的 flag / 徽章
     end   - 结局 key（出现则显示结局界面）
*/
const STORY = {
  title: "欧洲三大工人运动 · 见证者",
  subject: "101 · 政治 · 马原",
  author: "北大考研归档处",
  scene: "s_intro",
  scenes: {
    s_intro: {
      bg: "modern-library",
      text: "2026 年 4 月 · 北大图书馆\n\n你正翻着《红宝书》，马原章节，「马克思主义的三大思想来源」。书页下方一行小字：「伴随着三次工人运动的血与火——」\n\n突然，一束金色的光从书脊里涌出……",
      next: "s_flash"
    },
    s_flash: {
      bg: "warp",
      text: "你感到天旋地转。一瞬间，机器的轰鸣、煤烟的刺鼻、粗布的摩擦填满了你的感官。\n\n睁开眼时——\n\n你站在一条石板街上。远处是蒸汽机的轰鸣，头顶是阴沉的天空。",
      next: "s_lyon1"
    },
    s_lyon1: {
      bg: "lyon-street",
      name: "路人",
      face: "🧔",
      pos: "left",
      text: "喂！穿这么古怪！你是从哪个剧场跑出来的演员？这里是里昂，要打仗了，别挡路！",
      choices: [
        { text: "「这里是…里昂？几年？」", next: "s_lyon2" },
        { text: "「我来自 2026 年」", next: "s_lyon2b" }
      ]
    },
    s_lyon2: {
      bg: "lyon-street",
      name: "路人",
      face: "🧔",
      pos: "left",
      text: "1831 年冬。丝织工人今天要上街了。听说了吗？——「Vivre en travaillant, ou mourir en combattant」。「不能劳动而生，就要战斗而死」。",
      next: "s_workshop1"
    },
    s_lyon2b: {
      bg: "lyon-street",
      name: "路人",
      face: "🧔",
      pos: "left",
      text: "2026？呵，疯子。……算了，你要穿越就穿越，别耽误我的事。今天 1831 年，丝织工人要上街了。「不能劳动而生，就要战斗而死」——记住这句话。",
      next: "s_workshop1"
    },
    s_workshop1: {
      bg: "silk-workshop",
      name: "丝织工人",
      face: "⚒️",
      pos: "right",
      text: "（汗水从她的额头滴落到丝绸上）\n\n你看到什么了，小子？我每天坐在这织机前 14 个小时。孩子饿死在身边。老板一天赚我们全家一年的钱。",
      choices: [
        { text: "「这是你们咎由自取」", next: "s_bad_early" },
        { text: "「剥削的本质，就是剩余价值」", next: "s_awake", tag: "marx_aware" },
        { text: "「我该怎么帮你们？」", next: "s_awake" }
      ]
    },
    s_bad_early: {
      bg: "silk-workshop",
      name: "丝织工人",
      face: "⚒️",
      pos: "right",
      text: "（她冷冷地看着你）\n\n……滚出去。你这种人，和楼上那个老板是一伙的。\n\n（你被推搡着赶出工坊。在冷风中你意识到：历史从不为冷眼旁观者开分支。）",
      next: "s_end_bad_early"
    },
    s_end_bad_early: {
      bg: "fog",
      end: "bad_early",
      text: "【结局 · 冷眼旁观者】\n\n你在 1831 年的里昂冻饿而死。《红宝书》第 1 章的金线在历史中黯淡。你的名字从未出现在任何档案里。\n\n——未获得任何徽章"
    },
    s_awake: {
      bg: "silk-workshop",
      name: "丝织工人",
      face: "⚒️",
      pos: "right",
      text: "（她眼睛亮了一下）\n\n你是个有眼睛的人。明天，我们会上街。成千上万的工人。我们没有枪，只有黑旗。如果你懂我们——请替我们记住。",
      next: "s_uprising1"
    },
    s_uprising1: {
      bg: "uprising",
      text: "1831 年 11 月 21 日 · 里昂\n\n两万丝织工人涌上街头。黑旗上写着那句话。三天三夜，起义军占领了整座城市。\n\n但政府军最终用大炮镇压。600 人死去。火焰在罗讷河畔熄灭。",
      next: "s_uprising_q"
    },
    s_uprising_q: {
      bg: "uprising",
      text: "（穿越的金光又开始闪烁。历史的走廊在你面前展开——你必须答对一个问题，才能继续穿越。）\n\n【考点】19 世纪三四十年代，为马克思主义诞生奠定阶级基础的欧洲三大工人运动是：",
      choices: [
        { text: "法国里昂起义 + 英国宪章运动 + 德国西里西亚起义", next: "s_uprising_right", tag: "quiz_m1_pass" },
        { text: "巴黎公社 + 俄国十月革命 + 印度民族起义", next: "s_uprising_wrong" },
        { text: "波士顿茶党 + 法国大革命 + 明治维新", next: "s_uprising_wrong" }
      ]
    },
    s_uprising_right: {
      bg: "warp",
      text: "✓ 正确。\n\n金光环绕你。历史主动向你敞开它的脉络——\n\n你感到自己穿过一层膜，下一幕展开在眼前。",
      next: "s_chartism"
    },
    s_uprising_wrong: {
      bg: "fog",
      text: "✗ 历史线崩塌。\n\n这三个运动分别属于 1871 巴黎工人反政府、1917 俄国社会主义革命、1857 印度反英殖民——和三大工人运动的时间、性质都对不上。\n\n你在错误的时空里飘散。",
      next: "s_end_bad_quiz"
    },
    s_end_bad_quiz: {
      bg: "fog",
      end: "bad_quiz",
      text: "【结局 · 历史乱流】\n\n你在时空之间迷失。下次再来时请记住：19 世纪三四十年代，法国里昂、英国宪章、德国西里西亚——这是考研政治 101 马原第 1 章必背的「阶级基础」。\n\n——未获得任何徽章"
    },
    s_chartism: {
      bg: "london-rain",
      name: "宪章派工人",
      face: "🎩",
      pos: "left",
      text: "1836 年的伦敦，下着冷雨。我手里这份请愿书，上面有三百万个签名——占了英国成年男性的半数。\n\n我们要的不是面包——我们要普选权。「人民宪章」六条，会写进大英帝国的宪法。",
      next: "s_chartism2"
    },
    s_chartism2: {
      bg: "london-rain",
      name: "宪章派工人",
      face: "🎩",
      pos: "left",
      text: "但是议会驳回了我们的请愿——三次。1839、1842、1848。\n\n（他抹了把脸上的雨）\n\n运动失败了。但——我们第一次，作为「阶级」，发出了自己的声音。",
      next: "s_silesia1"
    },
    s_silesia1: {
      bg: "silesia-night",
      name: "西里西亚纺织工",
      face: "🧵",
      pos: "right",
      text: "1844 年 6 月 · 普鲁士西里西亚\n\n（她握着一把锤子，眼神像星火）\n\n今晚，我们要砸了这些机器。不是因为我们恨机器——是因为机器下面，压着我们孩子的尸体。",
      next: "s_silesia2"
    },
    s_silesia2: {
      bg: "silesia-night",
      text: "次日凌晨，普军开进村庄。十一个工人被就地枪决。\n\n但远在巴黎的一个叫卡尔·马克思的年轻人，听到消息时跳了起来：\n\n「这不是捣毁机器——这是工人第一次，作为阶级，宣告了自己的政治意识！」",
      next: "s_marx1"
    },
    s_marx1: {
      bg: "paris-study",
      name: "青年马克思",
      face: "marx_old",
      pos: "left",
      text: "（他的书房，满桌手稿。他转头看向你——穿越的人。）\n\n你看见了这三次起义。你告诉我——它们失败的共同原因是什么？",
      choices: [
        { text: "因为工人没有武器", next: "s_marx_wrong" },
        { text: "因为工人没有统一的理论指导", next: "s_marx_right", tag: "marx_theory" },
        { text: "因为资产阶级太强大", next: "s_marx_half" }
      ]
    },
    s_marx_wrong: {
      bg: "paris-study",
      name: "青年马克思",
      face: "marx_old",
      pos: "left",
      text: "武器？不。1831 年里昂的工人一度击溃了政府军，他们缺的从来不是武器。\n\n（他摇摇头）你还没看到本质。",
      next: "s_marx_right"
    },
    s_marx_half: {
      bg: "paris-study",
      name: "青年马克思",
      face: "marx_old",
      pos: "left",
      text: "资产阶级强大？——那是表象。你看到的是力量对比，没看到的是：工人阶级不知道自己为什么穷。\n\n没有理论，就不可能有自觉的运动。",
      next: "s_marx_right"
    },
    s_marx_right: {
      bg: "paris-study",
      name: "青年马克思",
      face: "marx_old",
      pos: "left",
      text: "对——他们缺的是理论。\n\n哲学家们只用不同的方式解释世界，问题在于——改变世界。\n\n（他把一本薄薄的小册子递给你）\n\n这个，会在 1848 年 2 月 24 日，伦敦，德文版，印出来。",
      next: "s_finale"
    },
    s_finale: {
      bg: "warp",
      text: "你手里的小册子封面烫着金字：\n\n《共产党宣言》\n\n三大工人运动用鲜血提出了问题。马克思主义用理论回答了它。这——就是考研红宝书第 1 章「阶级基础」的全部分量。\n\n（金光再次吞没你。下一瞬，你回到 2026 年的图书馆。手里还攥着那本小册子的体温。）",
      next: "s_end_good"
    },
    s_end_good: {
      bg: "modern-library",
      end: "good",
      text: "【结局 · 传火者】\n\n你见证了三大工人运动的全部。1831 里昂 / 1836 宪章 / 1844 西里西亚。\n\n你理解了：阶级基础 + 理论武装 = 马克思主义诞生的两条必经之路。\n\n——获得徽章「诞生徽章」（政治 M1）\n——获得隐藏物品「1848 宣言副本」\n\n回到现实世界，《红宝书》第 1 章对你来说不再是文字。"
    }
  }
};
