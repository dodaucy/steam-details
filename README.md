# Steam Details

Displays some details for a steam app or a whole wishlist.

Written to be used in the european union and tested in germany. If should be easy to modify this project to work in other countries if necessary.

## Disclaimer

This project is NOT affiliated with Steam. It is only for educational purposes.

## Showcase

You can hover over almost anything to see more details.

![Steam Details Showcase](./showcase.png)

## Installation

```bash
git clone https://github.com/dodaucy/steam-details.git
cd steam-details

pdm install  # https://pdm-project.org/latest/#installation
```

## Usage

```bash
pdm start
```

## Development

### Install dependencies

```bash
pdm install --dev
```

### Show lint errors

Run this command before committing.

```bash
pdm lint
```

### Fix fixable lint errors

Currently only import errors are fixed.

```bash
pdm fix
```
