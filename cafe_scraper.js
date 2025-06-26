// run this in the firefox js console while viewing the d20 games list pdf.
// zoom out to load all pages.
// copy the json object from the console to a file called games_db.json
// this will not get rid all of d20's comma alphabetising formatting, use "bgg".*\n.*"name": ".*,.* to find the last of them

function scrapePage(page)
{
  all_nodes = page.querySelectorAll(".textLayer > *");
  
  // group html nodes into games list entries
  grouped_nodes = [[]];
  all_nodes.forEach(node => 
  {
    if (node.tagName == "SPAN")
      grouped_nodes[grouped_nodes.length-1].push(node);
    else if (node.tagName == "BR")
      grouped_nodes.push([]);
  });
  grouped_nodes.splice(0, 4);

  // convert html nodes to raw data
  data = grouped_nodes.map(group =>
  {
    entry = [];
    
    group.forEach(node =>
    {
      node_text = node.innerText.trim();
      if (node_text != "")
        entry.push(node_text);
    });

    return entry;
  });

  // decipher glyphs used on d20 pdf to mark if game is an expansion and what kind it is
  data = data.map(entry =>
  {
    if (entry.length == 6) entry.splice(2, 0, "Base Game")

    if (entry.length == 8)
    {
      exp_syms = [entry[2], entry[3]]
      if (exp_syms.includes("⇲")) entry.splice(2, 2, "In Base Box");
      if (exp_syms.includes("+")) entry.splice(2, 2, "Base Required");
      if (exp_syms.includes("!")) entry.splice(2, 2, "Standalone");
    }

    return entry
  });

  // translate data from array to json object with headings
  headings = ["name", "category", "expansion_type", "shelf_id", "Num_of_players", "avg_playtime", "min_age"]
  data = data.map(in_entry => 
  {
    out_entry = {};
    for (i=0; i<7; i++)
    {
      out_entry[headings[i]] = in_entry[i];
    }
    return out_entry
  });

  // format json for help comparing data to bgg
  data = data.map(entry => 
  {
    // unformat names like "3 Commandments, The" and "Game Of Thrones, A: Catan" 
    bgg_name = entry["name"]
    reg_res = /(.*)(, (a|the)($|:))(.*)/ig.exec(bgg_name)
    if (reg_res)
      bgg_name = reg_res[3] + " " + reg_res[1] + reg_res[4] + reg_res[5];

    bgg_type = entry["expansion_type"] == "Base Game" ? "boardgame" : "boardgameexpansion";

    return {
      "d20" : entry,
      "bgg" : { "name" : bgg_name, "type" : bgg_type }
    }
  });
  
  return data
}

pages = document.querySelectorAll(".page > .textLayer");
data = [];
pages.forEach(page =>
{
  data = data.concat(scrapePage(page));
});

console.log(data);
