---
layout: page
title: People
permalink: /people/
---


<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
html {
  box-sizing: border-box;
}

*, *:before, *:after {
  box-sizing: inherit;
}

.column {
  float: left;
  width: 33.3%;
  margin-bottom: 16px;
  padding: 0 8px;
}

@media screen and (max-width: 650px) {
  .column {
    width: 100%;
    display: block;
  }
}

.card {
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
}

.container {
  padding: 0 16px;
}

.container::after, .row::after {
  content: "";
  clear: both;
  display: table;
}

.title {
  color: grey;
}

.button {
  border: none;
  outline: 0;
  display: inline-block;
  padding: 8px;
  color: white;
  background-color: #000;
  text-align: center;
  cursor: pointer;
  width: 100%;
}

.button:hover {
  background-color: #555;
}
</style>
</head>
<body>

<h2>Meet The Team</h2>
<br>

<div class="row">
  <div class="column">
    <div class="card">
      <img src="public/assets/ASD.jpeg" alt="Alberto" style="width:15%">
      <div class="container">
        <h2>Alberto Santos</h2>
        <p class="title">Group Lead</p>
        <p>Multi-omics Network Analytics &amp; Data Science Platform</p>
        <p>albsad[at]biosustain.dtu.dk</p>
      </div>
    </div>
  </div>

  <div class="column">
    <div class="card">
      <img src="public/assets/ALP.jpeg" alt="Angel" style="width:15%">
      <div class="container">
        <h2>Angel L. Panthanourak</h2>
        <p class="title">Research Assistant</p>
        <p>Multi-omics Network Analytics</p>
        <p>anglup[at]biosustain.dtu.dk</p>
      </div>
    </div>
  </div>
</body>
</html>

