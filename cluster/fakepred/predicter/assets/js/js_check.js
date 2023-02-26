var check = function () {
  if (
    document.getElementById("link").value.length != 0 &&
    (document.getElementById("title").value.length == 0 ||
      document.getElementById("content").value.length == 0)
  ) {
    document.getElementById("title").disabled = true;
    document.getElementById("content").disabled = true;
    document.getElementById("submit").disabled = false;
  } else if (
    document.getElementById("link").value.length == 0 &&
    (document.getElementById("title").value.length != 0 ||
      document.getElementById("content").value.length != 0)
  ) {
    document.getElementById("link").disabled = true;
    document.getElementById("submit").disabled = false;
  }
  if (
    document.getElementById("link").value.length == 0 &&
    document.getElementById("title").disabled == true &&
    document.getElementById("content").disabled == true
  ) {
    document.getElementById("title").disabled = false;
    document.getElementById("content").disabled = false;
    document.getElementById("submit").disabled = true;
  } else if (
    document.getElementById("title").value.length == 0 &&
    document.getElementById("content").value.length == 0 &&
    document.getElementById("link").disabled == true
  ) {
    document.getElementById("link").disabled = false;
    document.getElementById("submit").disabled = true;
  }
};

var valid = function () {
  document.getElementById("label").innerHTML = "Valid";
};

var fake = function () {
  document.getElementById("label").innerHTML = "Fake";
};

var check_submit = function () {};
