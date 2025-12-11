import modules.imgur as i

print("\n\n===============\n  Imgur Tests  \n===============\n\n")

print("Album with one image:")
print(i.get_image_for_embed("Timestamps: https://imgur.com/gallery/boooooo-G6znzYZ"))

print("\nAlbum with two images:")
print(i.get_image_for_embed("Timestamps: https://imgur.com/a/team-group-t-force-vulcanz-ddr4-ram-yUKZ5eX"))

print("\nAlbum with three images:")
print(i.get_image_for_embed("Timestamps: https://imgur.com/a/JZxOrAB"))

print("\nAlbum with four images:")
print(i.get_image_for_embed("Timestamps: https://imgur.com/a/hvuxgiv"))

print("\nAlbum with six images (should only use first four):")
print(i.get_image_for_embed("Timestamps: https://imgur.com/a/TtmNril"))

print("\nDirect image link:")
print(i.get_image_for_embed("Timestamps: https://i.imgur.com/32MkGOI.jpeg"))

print("\nAlbum with 3 images and 1 video (should not attempt to combine the video or return the video):")
print(i.get_image_for_embed("Timestamps: https://imgur.com/a/87r998p"))

print("\nInvalid album URL (should return None):")
print(i.get_image_for_embed("Timestamps: https://imgur.com/a/fhjaskfhaskfjsah"))
