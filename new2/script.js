// 顶部导航：移动端汉堡菜单切换
(function () {
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');

  if (!toggle || !links) return;

  toggle.addEventListener('click', function () {
    links.classList.toggle('open');
    toggle.classList.toggle('active');
  });

  // 点击导航链接后自动收起菜单
  links.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () {
      links.classList.remove('open');
      toggle.classList.remove('active');
    });
  });
})();
