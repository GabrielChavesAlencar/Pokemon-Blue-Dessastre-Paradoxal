# Replace only the pause-menu action. The title screen keeps its own Quit Game.
module BluePauseTitle
  def self.return_to_title(menu)
    menu.pbHideMenu
    if pbConfirmMessage(_INTL("Return to the main menu?"))
      PokemonSaveScreen.new(PokemonSave_Scene.new).pbSaveScreen
      menu.pbEndScene
      # Scene_Map processes this the same way as RPG Maker's Return to Title
      # command. This lets it dispose the map and call the normal title scene.
      $game_temp.title_screen_calling = true
      return true
    end
    menu.pbRefresh
    menu.pbShowMenu
    false
  end
end

MenuHandlers.add(:pause_menu, :quit_game, {
  "name"   => "Back to Main Menu",
  "order"  => 90,
  "effect" => proc { |menu| BluePauseTitle.return_to_title(menu) }
})
