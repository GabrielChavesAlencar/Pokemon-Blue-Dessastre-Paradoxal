# F02: render-only forest continuation in the verified private pilot.
module BlueSinnohForestEdge
  MAP_IDS=__F02_MAP_IDS__.freeze
  TEXTURE="Graphics/Tilesets/SNQA_ForestEdge.png".freeze

  def self.active?
    defined?(BlueSinnohExperimental) &&
      BlueSinnohExperimental.private_copy? &&
      $game_map && MAP_IDS.include?($game_map.map_id)
  end

  module Renderer
    def update(*args,&block)
      result=super
      blue_sinnoh_forest_update
      result
    end

    def blue_sinnoh_forest_update
      unless BlueSinnohForestEdge.active?
        @blue_sinnoh_forest_sprites&.each_value { |sprite| sprite.visible=false }
        return
      end
      @blue_sinnoh_forest_sprites ||= {}
      @blue_sinnoh_forest_bitmap ||= Bitmap.new(BlueSinnohForestEdge::TEXTURE)
      # The native renderer already resolves the current map AND connected
      # neighbours. Its three-layer blank stacks are exactly the void cells.
      # Never paint over a real tile, even if that tile has transparent pixels.
      @blue_sinnoh_forest_sprites.each_value { |sprite| sprite.visible=false }
      @tiles.each_with_index do |col,i|
        col.each_with_index do |stack,j|
          next unless stack.all? { |tile| tile.tile_id && tile.tile_id<48 }
          key=[i,j]
          sprite=@blue_sinnoh_forest_sprites[key]
          unless sprite
            sprite=Sprite.new(@viewport)
            sprite.bitmap=@blue_sinnoh_forest_bitmap
            sprite.z=-1000
            sprite.zoom_x=TilemapRenderer::ZOOM_X
            sprite.zoom_y=TilemapRenderer::ZOOM_Y
            @blue_sinnoh_forest_sprites[key]=sprite
          end
          # Match native renderer positioning at tile and subpixel scroll.
          sprite.x=i*TilemapRenderer::DISPLAY_TILE_WIDTH-@pixel_offset_x
          sprite.y=j*TilemapRenderer::DISPLAY_TILE_HEIGHT-@pixel_offset_y
          sprite.src_rect.set(((@tile_offset_x+i)%2)*32,
                              ((@tile_offset_y+j)%2)*32,32,32)
          sprite.tone=@tone
          sprite.color=@color
          sprite.visible=true
        end
      end
    end

    def dispose(*args,&block)
      if @blue_sinnoh_forest_sprites
        @blue_sinnoh_forest_sprites.each_value { |s| s.dispose unless s.disposed? }
        @blue_sinnoh_forest_sprites.clear
      end
      if @blue_sinnoh_forest_bitmap && !@blue_sinnoh_forest_bitmap.disposed?
        @blue_sinnoh_forest_bitmap.dispose
      end
      @blue_sinnoh_forest_bitmap=nil
      super
    end
  end

  def self.install!
    return unless defined?(BlueSinnohExperimental) &&
      BlueSinnohExperimental.private_copy? && defined?(TilemapRenderer) &&
      TilemapRenderer.method_defined?(:update) && TilemapRenderer.method_defined?(:dispose)
    TilemapRenderer.prepend(Renderer) unless TilemapRenderer.ancestors.include?(Renderer)
  end
end
