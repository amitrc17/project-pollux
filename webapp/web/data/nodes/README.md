An Asset Forest is a representation of the possessions of a user
as tracked by Pollux. The entire forest belongs to 1 user. Every
Tree in the forest is rooted at a relatively high level category. We
cannot predict all categories, so they are always dynamically created.

All non-leaf nodes in the forest are Descriptors, however some Descriptors
might be leaf nodes. Descriptors that are leaf nodes indicate the User does
not possess any Asset fitting that Description. Descriptors may describe:
Location, Usage, Physical Attributes, Compositional Attributes, and any
other categorical information. Descriptors are tailored to the single
owner User, i.e 2 users may have the same Descriptor that has different
paths from the User to that particular Descriptor.
We will eventually use domain knowledge, user input
and ML to split and splice Descriptors.

Assets are leaf nodes. These represent the User's possessions. These likely
came from User inputs: image, text, chat.